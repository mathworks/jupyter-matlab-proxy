# Copyright 2026 The MathWorks, Inc.

from . import ActionCommand, ActionTypes
from pathlib import Path


class CheckFileExistsAction(ActionCommand):
    def __init__(self, kernel):
        self.kernel = kernel
        self.log = kernel.log

    def validate_data(self, data):
        if "ipynbFilePath" not in data:
            raise ValueError(
                "Invalid data for CheckFileExistsAction: 'ipynbFilePath' is required."
            )

    async def execute(self, comm, data):
        """Starts MATLAB proxy
        Args:
            comm (ipykernel.comm.Comm): IPYKernels' Commuincation object
        """
        try:
            self.validate_data(data)

        except ValueError as ve:
            self.log.error(f"CheckFileExists action validation failed with error: {ve}")
            comm.send(
                {
                    "action": ActionTypes.CHECK_FILE_EXISTS.value,
                    "exists": False,
                    "error": str(ve),
                }
            )
            return

        ipynb_filepath = data.get("ipynbFilePath", "")

        self.log.debug(f"File to check if it exists: {ipynb_filepath}")

        if not ipynb_filepath:
            error_msg = "No file path provided for checking if it exists"
            self.log.error(error_msg)
            comm.send(
                {
                    "action": ActionTypes.CHECK_FILE_EXISTS.value,
                    "exists": False,
                    "error": error_msg,
                }
            )

        else:
            ipynb_filepath = Path(ipynb_filepath).expanduser()
            livecode_m_filepath = ipynb_filepath.parent / (ipynb_filepath.stem + ".m")

            self.log.debug(
                f"LiveCode file at {livecode_m_filepath} exists: {livecode_m_filepath.exists()}"
            )

            comm.send(
                {
                    "action": ActionTypes.CHECK_FILE_EXISTS.value,
                    "exists": livecode_m_filepath.exists(),
                    "error": None,
                }
            )
