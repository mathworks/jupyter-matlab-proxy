# Copyright 2023-2025 The MathWorks, Inc.

"""
This module serves as the base class for various MATLAB Kernels.
Examples of supported Kernels can be:
1. MATLAB Kernels that are based on Jupyter Server and Jupyter Server proxy to start
backend MATLAB proxy servers.
2. MATLAB Kernels that uses proxy manager to start backend matlab proxy servers
"""

import os
import sys
import time
from logging import Logger
from pathlib import Path

import aiohttp
import aiohttp.client_exceptions
import ipykernel.kernelbase
import psutil
from matlab_proxy import settings as mwi_settings
from matlab_proxy import util as mwi_util

from jupyter_matlab_kernel.magic_execution_engine import (
    MagicExecutionEngine,
    get_completion_result_for_magics,
)
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError

from jupyter_matlab_kernel.comms import LabExtensionCommunication


_MATLAB_STARTUP_TIMEOUT = mwi_settings.get_process_startup_timeout()


def _fetch_jupyter_base_url(parent_pid: str, logger: Logger) -> str:
    """
    Fetches information about the running Jupyter server associated with the MATLAB kernel.

    This function attempts to retrieve the list of running Jupyter servers and identify the
    server associated with the current MATLAB kernel based on its parent process ID. If the
    Jupyter server is found, it attempts to fetch the base URL of that Jupyter Server.

    Args:
        parent_pid: process ID (PID) of the Kernel's parent process.
        logger (Logger): The logger instance for logging debug information.

    Returns:
        base_url (str): The base URL of the Jupyter server, if found.
    """
    nb_server_list = []
    try:
        from jupyter_server import serverapp

        nb_server_list += list(serverapp.list_running_servers())

        from notebook import notebookapp

        nb_server_list += list(notebookapp.list_running_servers())
    except ImportError:
        pass

    nb_server = {}
    found_nb_server = False
    for server in nb_server_list:
        if server["pid"] == parent_pid:
            found_nb_server = True
            nb_server = server
            # Stop iterating over the server list
            return nb_server["base_url"]

    # log and return empty string if the server is not found
    if not found_nb_server:
        logger.debug(
            "Jupyter server associated with this MATLAB Kernel not found, might a non-jupyter based MATLAB Kernel"
        )
    return ""


def _get_parent_pid() -> int:
    """
    Retrieves the parent process ID (PID) of the Kernel process.

    This function determines the process ID of the parent (Jupyter/VSCode) that spawned the
    current kernel. On Windows platforms using virtual environments, it accounts for an
    intermediate process that may spawn the kernel, by going one level higher in the process
    hierarchy to obtain the correct parent PID.

    Returns:
        str: The PID of the Jupyter server.
    """
    parent_pid = os.getppid()

    # Note: conda environments do not require this, and for these environments
    # sys.prefix == sys.base_prefix
    is_virtual_env = sys.prefix != sys.base_prefix
    if mwi_util.system.is_windows() and is_virtual_env:
        parent_pid = psutil.Process(parent_pid).ppid()
    return parent_pid


class BaseMATLABKernel(ipykernel.kernelbase.Kernel):
    # Required variables for Jupyter Kernel to function
    # banner is shown only for Jupyter Console.
    banner = "MATLAB"
    implementation = "jupyter_matlab_kernel"
    implementation_version: str = "0.0.1"

    # Values should be same as Codemirror mode
    language_info = {
        "name": "matlab",
        "mimetype": "text/x-matlab",
        "file_extension": ".m",
    }

    def __init__(self, *args, **kwargs):
        # Call superclass constructor to initialize ipykernel infrastructure
        super().__init__(*args, **kwargs)

        # Kernel identifier which is used to setup loggers as well as to track the
        # mapping between this kernel and the backend MATLAB proxy process when proxy-manager
        # is used as the MATLAB proxy provisioner.
        self.kernel_id = self._extract_kernel_id_from_sys_args(sys.argv)

        # Provides the base_url for the matlab-proxy which is assigned to this Kernel instance
        self.matlab_proxy_base_url = ""

        # Used to track if there was any errors during MATLAB proxy startup
        self.startup_error = None

        # base_url field for Jupyter Server, required for performing licensing
        self.jupyter_base_url = None

        # Keeps track of whether the startup checks were completed or not
        self.startup_checks_completed: bool = False

        self.log.debug(f"Initializing kernel with id: {self.kernel_id}")
        self.log = self.log.getChild(f"{self.kernel_id}")

        # Initialize the Magic Execution Engine.
        self.magic_engine = MagicExecutionEngine(self.log)

        # Communication helper for interaction with backend MATLAB proxy
        self.mwi_comm_helper = None

        self.labext_comm = LabExtensionCommunication(self)

        # Custom handling of comm messages for jupyterlab extension communication.
        # https://jupyter-client.readthedocs.io/en/latest/messaging.html#custom-messages

        # Override only comm handlers to keep implementation clean by separating
        # JupyterLab extension communication logic from core kernel functionality.
        # Other handlers (interrupt_request, execute_request, etc.) remain in base class.
        self.shell_handlers["comm_open"] = self.labext_comm.comm_open
        self.shell_handlers["comm_msg"] = self.labext_comm.comm_msg
        self.shell_handlers["comm_close"] = self.labext_comm.comm_close

    # ipykernel Interface API
    # https://ipython.readthedocs.io/en/stable/development/wrapperkernels.html

    async def interrupt_request(self, stream, ident, parent):
        """
        Custom handling of interrupt request sent by Jupyter. For more info, look at
        https://jupyter-client.readthedocs.io/en/stable/messaging.html#kernel-interrupt
        """
        self.log.debug("Received interrupt request from Jupyter")
        try:
            # Send interrupt request to MATLAB
            await self.mwi_comm_helper.send_interrupt_request_to_matlab()

            # Set the response to interrupt request.
            content = {"status": "ok"}
        except Exception as e:
            # Set the exception information as response to interrupt request
            self.log.error(
                f"Exception occurred while sending interrupt request to MATLAB: {e}"
            )
            content = {
                "status": "error",
                "ename": str(type(e).__name__),
                "evalue": str(e),
                "traceback": [],
            }

        self.session.send(stream, "interrupt_reply", content, parent, ident=ident)

    def modify_kernel(self, states_to_modify):
        """
        Used to modify MATLAB Kernel state
        Args:
            states_to_modify (dict): A key value pair of all the states to be modified.

        """
        self.log.debug(f"Modifying the kernel with {states_to_modify}")
        for key, value in states_to_modify.items():
            if hasattr(self, key):
                self.log.debug(f"set the value of {key} to {value}")
                setattr(self, key, value)

    def handle_magic_output(self, output, outputs=None):
        if output["type"] == "modify_kernel":
            self.modify_kernel(output)
        else:
            self.display_output(output)
            if outputs is not None and not self.startup_checks_completed:
                # Outputs are cleared after startup_check.
                # Storing the magic outputs to display them after startup_check completes.
                outputs.append(output)

    async def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
        *,
        cell_id=None,
    ):
        """
        Used by ipykernel infrastructure for execution. For more info, look at
        https://jupyter-client.readthedocs.io/en/stable/messaging.html#execute
        """
        self.log.debug(f"Received execution request from Jupyter with code:\n{code}")
        try:
            accumulated_magic_outputs = []
            performed_startup_checks = False

            for output in self.magic_engine.process_before_cell_execution(
                code, self.execution_count
            ):
                self.handle_magic_output(output, accumulated_magic_outputs)

            skip_cell_execution = self.magic_engine.skip_cell_execution()
            self.log.debug(f"Skipping cell execution is set to {skip_cell_execution}")

            # Complete one-time startup checks before sending request to MATLAB.
            # Blocking call, returns after MATLAB is started.
            if not skip_cell_execution:
                if not self.startup_checks_completed:
                    await self.perform_startup_checks()
                    self.display_output(
                        {
                            "type": "stream",
                            "content": {
                                "name": "stdout",
                                "text": "Executing ...",
                            },
                        }
                    )
                    if accumulated_magic_outputs:
                        self.display_output(
                            {"type": "clear_output", "content": {"wait": False}}
                        )
                    performed_startup_checks = True
                    self.startup_checks_completed = True

                if performed_startup_checks and accumulated_magic_outputs:
                    for output in accumulated_magic_outputs:
                        self.display_output(output)

                # Perform execution and categorization of outputs in MATLAB. Blocks
                # until execution results are received from MATLAB.
                outputs = await self.mwi_comm_helper.send_execution_request_to_matlab(
                    code
                )

                if performed_startup_checks and not accumulated_magic_outputs:
                    self.display_output(
                        {"type": "clear_output", "content": {"wait": False}}
                    )

                self.log.debug(
                    "Received outputs after execution in MATLAB. Clearing output area"
                )

                # Display all the outputs produced during the execution of code.
                for idx in range(len(outputs)):
                    data = outputs[idx]
                    self.log.debug(f"Displaying output {idx+1}:\n{data}")

                    # Ignore empty values returned from MATLAB.
                    if not data:
                        continue
                    self.display_output(data)

            # Execute post execution of MAGICs
            for output in self.magic_engine.process_after_cell_execution():
                self.handle_magic_output(output)

        except Exception as e:
            self.log.error(
                f"Exception occurred while processing execution request:\n{e}"
            )
            if isinstance(e, aiohttp.client_exceptions.ClientError):
                # Log the ClientError for debugging
                self.log.error(e)

                # If exception is an ClientError, it means MATLAB is unavailable.
                # Replace the ClientError with MATLABConnectionError to give
                # meaningful error message to the user
                e = MATLABConnectionError()

                # Since MATLAB is not available, we need to perform the startup
                # checks for subsequent execution requests
                self.startup_checks_completed = False

            # Clearing lingering message "Executing..." before displaying the error message
            if performed_startup_checks and not accumulated_magic_outputs:
                self.display_output(
                    {"type": "clear_output", "content": {"wait": False}}
                )
            # Send the exception message to the user.
            self.display_output(
                {
                    "type": "stream",
                    "content": {
                        "name": "stderr",
                        "text": str(e),
                    },
                }
            )
        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    async def do_complete(self, code, cursor_pos):
        """
        Used by ipykernel infrastructure for tab completion. For more info, look
        at https://jupyter-client.readthedocs.io/en/stable/messaging.html#completion

        Note: Apart from completion results, no other data can be presented to
              user. For example, if matlab-proxy is not licensed, we cannot show
              the licensing window.
        """
        self.log.debug(
            f"Received completion request from Jupyter with cursor position {cursor_pos} and code:\n{code}"
        )
        # Default completion results. It is modelled after ipkernel.py#do_complete
        # implementation to provide metadata for JupyterLab.
        completion_results = {
            "matches": [],
            "start": cursor_pos,
            "end": cursor_pos,
            "completions": [],
        }

        # Fetch tab completion results. Blocks untils either tab completion
        # results are received from MATLAB or communication with MATLAB fails.

        magic_completion_results = get_completion_result_for_magics(
            code, cursor_pos, self.log
        )

        self.log.debug(
            f"Received Completion results from MAGIC:\n{magic_completion_results}"
        )

        if magic_completion_results:
            completion_results = magic_completion_results
        else:
            try:
                completion_results = (
                    await self.mwi_comm_helper.send_completion_request_to_matlab(
                        code, cursor_pos
                    )
                )
            except (
                MATLABConnectionError,
                aiohttp.client_exceptions.ClientResponseError,
            ) as e:
                self.log.error(
                    f"Exception occurred while sending completion request to MATLAB:\n{e}"
                )

            self.log.debug(
                f"Received completion results from MATLAB:\n{completion_results}"
            )

        return {
            "status": "ok",
            "matches": completion_results["matches"],
            "cursor_start": completion_results["start"],
            "cursor_end": completion_results["end"],
            "metadata": {
                "_jupyter_types_experimental": completion_results["completions"]
            },
        }

    async def do_is_complete(self, code):
        # TODO: Seems like indentation rules. https://jupyter-client.readthedocs.io/en/stable/messaging.html#code-completeness
        return super().do_is_complete(code)

    async def do_inspect(self, code, cursor_pos, detail_level=0, omit_sections=...):
        # TODO: Implement Shift+Tab functionality. Can be used to provide any contextual information.
        return super().do_inspect(code, cursor_pos, detail_level, omit_sections)

    async def do_history(
        self,
        hist_access_type,
        output,
        raw,
        session=None,
        start=None,
        stop=None,
        n=None,
        pattern=None,
        unique=False,
    ):
        # TODO: Implement accessing history in Notebook. Usually this history is related to the code typed in notebook.
        # However, we may also choose to associate with MATLAB History stored on disk.
        return super().do_history(
            hist_access_type, output, raw, session, start, stop, n, pattern, unique
        )

    # Helper functions

    def display_output(self, out):
        """
        Common function to send execution outputs to Jupyter UI.
        For more information, look at https://jupyter-client.readthedocs.io/en/stable/messaging.html#messages-on-the-iopub-pub-sub-channel

        Input Example:
        1.  Execution Output:
            out = {
                "type": "execute_result",
                "mimetype": ["text/plain","text/html"],
                "value": ["Hello","<html><body>Hello</body></html>"]
            }
        2.  For all other message types:
            out = {
                "type": "stream",
                "content": {
                    "name": "stderr",
                    "text": "An error occurred"
                }
            }

        Args:
            out (dict): A dictionary containing the type of output and the content of the output.
        """
        msg_type = out["type"]
        if msg_type == "execute_result":
            assert len(out["mimetype"]) == len(out["value"])
            response = {
                # Use zip to create a tuple of KV pair of mimetype and value.
                "data": dict(zip(out["mimetype"], out["value"])),
                "metadata": {},
                "execution_count": self.execution_count,
            }
        else:
            response = out["content"]
        self.send_response(self.iopub_socket, msg_type, response)

    async def perform_startup_checks(
        self, jupyter_base_url="", matlab_proxy_base_url=""
    ):
        """
        One time checks triggered during the first execution request. Displays
        login window if matlab is not licensed using matlab-proxy.

        Raises:
            ClientError, MATLABConnectionError: Occurs when matlab-proxy is not started or
                                              kernel cannot communicate with MATLAB.
        """
        self.log.debug("Performing startup checks")
        # In case an error occurred while kernel initialization, display it to the user.
        if self.startup_error is not None:
            self.log.error(f"Found a startup error: {self.startup_error}")
            raise self.startup_error

        (
            is_matlab_licensed,
            matlab_status,
            matlab_proxy_has_error,
        ) = await self.mwi_comm_helper.fetch_matlab_proxy_status()

        # Display iframe containing matlab-proxy to show login window if MATLAB
        # is not licensed using matlab-proxy. The iframe is removed after MATLAB
        # has finished startup.
        #
        # This approach does not work when using the kernel in VS Code. We are using relative path
        # as src for iframe to avoid hardcoding any hostname/domain information. This is done to
        # ensure the kernel works in Jupyter deployments. VS Code however does not work the same way
        # as other browser based Jupyter clients.
        if not is_matlab_licensed:
            if not jupyter_base_url:
                # happens for non-jupyter environments (like VSCode), we expect licensing to
                # be completed before hand
                self.log.debug(
                    "MATLAB is not licensed and is in a non-jupyter environment. licensing via other means required."
                )
                raise MATLABConnectionError(
                    """
                    Error: Cannot start MATLAB as no licensing information was found. 
                    Resolution: Set the environment variable MLM_LICENSE_FILE to provide a network license manager, 
                    or set MWI_USE_EXISTING_LICENSE to True if the installed MATLAB is already licensed. 
                    See https://github.com/mathworks/matlab-proxy/blob/main/Advanced-Usage.md for more information.
                    To use Online licensing, start a MATLAB Kernel in a Jupyter notebook and login using the web interface 
                    shown upon execution of any code.
                    """
                )
            self.log.debug(
                "MATLAB is not licensed. Displaying HTML output to enable licensing."
            )
            self.display_output(
                {
                    "type": "display_data",
                    "content": {
                        "data": {
                            "text/html": f'<iframe src={matlab_proxy_base_url} width=700 height=600"></iframe>'
                        },
                        "metadata": {},
                    },
                }
            )

        # Wait until MATLAB is started before sending requests.
        await self.poll_for_matlab_startup(
            is_matlab_licensed, matlab_status, matlab_proxy_has_error
        )

    async def poll_for_matlab_startup(
        self, is_matlab_licensed, matlab_status, matlab_proxy_has_error
    ):
        """Wait until MATLAB has started or time has run out"

        Args:
        is_matlab_licensed (bool): A flag indicating whether MATLAB is
            licensed and eligible to start.
        matlab_status (str): A string representing the current status
            of the MATLAB startup process.
        matlab_proxy_has_error (bool): A flag indicating whether there
            is an error in the MATLAB proxy process during startup.

        Raises:
            MATLABConnectionError: If an error occurs while attempting to
            connect to the MATLAB backend, or if MATLAB fails to start
            within the expected timeframe.
        """
        self.log.debug("Waiting until MATLAB is started")
        timeout = 0
        while (
            matlab_status != "up"
            and timeout != _MATLAB_STARTUP_TIMEOUT
            and not matlab_proxy_has_error
        ):
            if is_matlab_licensed:
                if timeout == 0:
                    self.log.debug("Licensing completed. Clearing output area")
                    self.display_output(
                        {"type": "clear_output", "content": {"wait": False}}
                    )
                    self.display_output(
                        {
                            "type": "stream",
                            "content": {
                                "name": "stdout",
                                "text": "Starting MATLAB ...\n",
                            },
                        }
                    )
                timeout += 1
            time.sleep(1)
            (
                is_matlab_licensed,
                matlab_status,
                matlab_proxy_has_error,
            ) = await self.mwi_comm_helper.fetch_matlab_proxy_status()

        # If MATLAB is not available after 15 seconds of licensing information
        # being available either through user input or through matlab-proxy cache,
        # then display connection error to the user.
        if timeout == _MATLAB_STARTUP_TIMEOUT:
            self.log.error(
                f"MATLAB has not started after {_MATLAB_STARTUP_TIMEOUT} seconds."
            )
            raise MATLABConnectionError

        if matlab_proxy_has_error:
            self.log.error("matlab-proxy encountered error.")
            raise MATLABConnectionError

        self.log.debug("MATLAB is running, startup checks completed.")

    def _extract_kernel_id_from_sys_args(self, args) -> str:
        """
        Extracts the kernel ID from the system arguments.

        This function parses the system arguments to extract the kernel ID from the Jupyter
        kernel connection file path. The expected format of the arguments is:
        ['/path/to/jupyter_matlab_kernel/__main__.py', '-f', '/path/to/kernel-<kernel_id>.json'].
        If the extraction fails, it logs a debug message and returns another identifier (self.ident)
        from the kernel base class.

        Args:
            args (list): The list of system arguments.

        Returns:
            str: The extracted kernel ID if successful, otherwise `self.ident`.

        Notes:
            self.ident is another random UUID and is not as same as kernel id which we are using
            for logs correlation as well as mapping the backend MATLAB proxy to a MATLAB Kernel
            at proxy manager layer. Users will not be able to route to their corresponding MATLAB
            when they click "Open MATLAB" button from their notebook interface, for isolated MATLAB.
            As of now, connection file name is the only source of truth that supplies the kernel id
            correctly. The issue of not being able to route to corresponding MATLAB is only specific
            to Jupyter (via Jupyter Server Proxy) and specifically in isolated MATLAB workflows and
            won't have impact on VSCode or other clients (e.g. test client).

        """
        try:
            connection_file_path: Path = Path(args[2])

            # Get the final component of the path without the suffix
            kernel_file_name = connection_file_path.stem

            # Jupyter kernel connection file naming scheme -> kernel-a8623c0a-574e-4f3d-a03a-ccb8c3f21165.json
            # VSCode kernel connection file naming scheme -> kernel-v2-3030095VYYhRYlRs0Eu.json
            return kernel_file_name.split("kernel-")[1]
        except Exception as e:
            self.log.debug(
                f"Unable to extract kernel id from the sys args with ex: {e}"
            )
            return self.ident
