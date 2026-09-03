# Copyright 2026 The MathWorks, Inc.

from . import ActionCommand, ActionTypes
from pathlib import Path
import asyncio
import re
import time


class EditAction(ActionCommand):
    def __init__(self, kernel):
        self.kernel = kernel
        self.log = kernel.log

    def get_code(self, mlx_file_path):
        """Fetches code specific to Edit action.

        Args:
            mlx_file_path (str): MLX file path to be opened in MATLAB.

        Returns:
            str: MATLAB code which opens the MLX file in MATLAB.
        """
        return f"edit('{mlx_file_path}');"

    def __check_if_rootapp_instance_is_set(self, string):
        match = re.search(r"^\s*State:\s*(\S+)", string, re.MULTILINE)
        if match:
            state = match.group(1)
            return state == "RUNNING"
        else:
            raise Exception("Failed to parse response string from MATLAB")

    async def __wait_for_rootapp_instance_to_be_set(self):
        # MATLAB try/catch so the trace never surfaces; on failure we report the
        # instance as still initializing so the loop below simply retries until it is
        # ready (or the timeout below fires), matching the pre-existing retry behavior.
        # `getInstance()` is intentionally left unterminated so its display output
        # (which carries the "State: RUNNING" line we parse) is emitted. `clear ans;`
        # is placed after `end` so it always runs, even when `getInstance()` throws
        # and control jumps to the catch block (MATLAB has no `finally`).
        getinstance_code = (
            "try\n"
            "matlab.ui.container.internal.RootApp.getInstance()\n"
            "catch\n"
            "disp('State: INITIALIZING')\n"
            "end\n"
            "clear ans;"
        )
        # Wait for the JSD to start loading before sending the root app instance.
        # If request is sent too early, any commands executed will have their outputs missing
        # TODO:Remove this sleep after the above bug is fixed.
        self.log.debug(f"Waiting for 5 seconds before sending rootapp request")
        await asyncio.sleep(5)

        time_taken, time_out = 0, 30
        # Keep checking if instance is set
        while True:

            try:
                self.log.debug(
                    "Waiting for an additional 1 second every time before sending the request"
                )
                await asyncio.sleep(1)
                eval_response = (
                    await self.kernel.mwi_comm_helper.send_eval_request_to_matlab(
                        getinstance_code
                    )
                )

                if eval_response["isError"]:
                    # Transient during JSD startup; the loop retries until
                    # the RootApp instance is ready. Logged at debug level to avoid alarming
                    # users with an expected, self-healing condition.
                    self.log.debug(
                        f"RootApp instance not ready yet, retrying. Response: {eval_response['responseStr']}"
                    )

                else:
                    if self.__check_if_rootapp_instance_is_set(
                        eval_response["responseStr"]
                    ):
                        self.log.debug("Rootapp instance is set is in use")
                        # Sleep for a second to ensure desktop state is confirmed.
                        break
                    else:
                        self.log.info("Root app instance is initializing, retrying...")

            except Exception as err:
                self.log.error(f"Edit action failed with error: {err}")
                raise err

            finally:
                time_taken += 1
                if time_taken > time_out:
                    err = TimeoutError(
                        f"Failed to set client type within {time_out} seconds."
                    )
                    self.log.error(err)
                    raise err

    async def __send_edit_request(self, comm, mlx_file_path):
        # Client type is set on the jsd, now send eval request to open mlx file
        code = self.get_code(mlx_file_path)
        # Sleeping for a second after client type is set for always ensuring JS tabs open
        # and not java ones
        await asyncio.sleep(1)
        eval_response = await self.kernel.mwi_comm_helper.send_eval_request_to_matlab(
            code
        )
        self.log.debug(f"Edit action eval response: {eval_response}")
        if eval_response["isError"]:
            err = Exception(
                f"Failed to send edit request with error: {eval_response['responseStr']}"
            )
            self.log.error(str(err))
            raise err

        else:
            comm.send({"action": ActionTypes.EDIT.value, "error": None})
            self.log.debug("Edit action successful")

    def validate_data(self, data):
        if "liveCodeFilePath" not in data:
            raise ValueError(
                "Invalid data for EditAction: 'liveCodeFilePath' is required."
            )

    async def execute(self, comm, data):
        """Executes the Edit action based on the data provided and returns
        result to the labextension using the comm channel.

        Args:
            comm (ipykernel.comm.Comm): IPYKernels' Commuincation object
            data (dict): data used by this action

        Raises:
            err: FileNotFoundError error if no MLX file path is supplied
        """

        # For Edit, we need to ensure that MATLAB is up and running.
        # This check is not performed here as it already done by the labextension before
        # sending the request to the kernel.
        try:
            self.validate_data(data)

        except ValueError as ve:
            self.log.error(f"Edit action validation failed with error: {ve}")
            # Inform lab extension about the error
            comm.send(
                {
                    "action": ActionTypes.EDIT.value,
                    "error": str(ve),
                }
            )
            return

        livecode_filepath = Path(data["liveCodeFilePath"]).expanduser()
        self.log.info(
            f"Received Live Script file path for opening in the editor: {livecode_filepath}"
        )

        try:
            # Checking for RootApp instance to be set
            # Takes 7 seconds in 25a and 7 seconds in 24b.
            await self.__wait_for_rootapp_instance_to_be_set()

            await self.__send_edit_request(comm, livecode_filepath)

        except Exception as err:
            comm.send({"action": ActionTypes.EDIT.value, "error": str(err)})
