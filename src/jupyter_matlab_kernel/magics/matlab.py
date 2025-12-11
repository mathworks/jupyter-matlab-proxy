# Copyright 2025 The MathWorks, Inc.

from jupyter_matlab_kernel.magics.base.matlab_magic import MATLABMagic
from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM
from jupyter_matlab_kernel.mwi_exceptions import MagicError

# Module constants
LICENSING_MODES = {
    "mhlm": "Online Licensing",
    "nlm": "Network License Manager",
    "existing_license": "Existing License",
}
CMD_NEW_SESSION = "new_session"
CMD_INFO = "info"
EXISTING_NEW_SESSION_ERROR = "This kernel is already using a dedicated MATLAB.\n"
DEDICATED_SESSION_CONFIRMATION_MSG = (
    "A dedicated MATLAB session has been started for this kernel.\n"
)


async def handle_new_matlab_session(kernel: MATLABKernelUsingMPM):
    """
    Handles the creation of a new dedicated MATLAB session for the kernel.
    Args:
        kernel: The kernel instance.

    Yields:
        dict: Result dictionary containing execution status and confirmation message.
    """
    # Validations
    if kernel.is_matlab_assigned:
        if not kernel.is_shared_matlab:
            # No-op if already in an isolated MATLAB session
            yield {
                "type": "execute_result",
                "mimetype": ["text/plain", "text/html"],
                "value": [
                    EXISTING_NEW_SESSION_ERROR,
                    f"<html><body><pre>{EXISTING_NEW_SESSION_ERROR}</pre></body></html>",
                ],
            }
            return

        else:
            # Shared MATLAB session is already assigned
            kernel.log.warning(
                "Cannot start a new MATLAB session while an existing session is active."
            )
            raise MagicError(
                "This notebook is currently linked to Default MATLAB session."
                "To proceed, restart the kernel and run this magic command before any other MATLAB commands."
            )
    # Starting new dedicated MATLAB session
    try:
        kernel.is_shared_matlab = False
        await kernel.start_matlab_proxy_and_comm_helper()
        kernel.is_matlab_assigned = True

        # Raises MATLABConnectionError if matlab-proxy failed to start in previous step
        await kernel.perform_startup_checks()
        kernel.startup_checks_completed = True
        kernel.display_output({"type": "clear_output", "content": {"wait": False}})
    except Exception as ex:
        _reset_kernel_state(kernel)

        # Try and cleanup the matlab-proxy process if it was started
        await kernel.cleanup_matlab_proxy()

        # Raising here so that matlab magic output can display the error
        raise MagicError(str(ex)) from ex

    yield {
        "type": "execute_result",
        "mimetype": ["text/plain", "text/html"],
        "value": [
            DEDICATED_SESSION_CONFIRMATION_MSG,
            f"<html><body><pre>{DEDICATED_SESSION_CONFIRMATION_MSG}</pre></body></html>",
        ],
    }


def _reset_kernel_state(kernel: MATLABKernelUsingMPM):
    """
    Resets the kernel to its initial state for MATLAB session management.

    Args:
        kernel (MATLABKernelUsingMPM): The MATLAB kernel instance whose state
                                       needs to be reset.
    """
    kernel.is_shared_matlab = True
    kernel.is_matlab_assigned = False
    kernel.startup_checks_completed = False


async def get_kernel_info(kernel):
    """
    Provides information about the current MATLAB kernel state related to MATLAB.

    :param kernel: kernel object containing MATLAB information
    """
    output = _format_info(kernel._get_kernel_info())
    yield {
        "type": "execute_result",
        "mimetype": ["text/plain", "text/html"],
        "value": [
            output,
            f"<html><body><pre>{output}</pre></body></html>",
        ],
    }


def _format_info(info) -> str:
    """
    Formats MATLAB information into a formatted string.

    Args:
        info: Dictionary containing MATLAB information.

    Returns:
        str: Formatted string with MATLAB information.
    """
    info_text = f'MATLAB Version: {info.get("matlab_version")}\n'
    info_text += f'MATLAB Root Path: {info.get("matlab_root_path")}\n'
    info_text += f'Licensing Mode: {LICENSING_MODES.get(info.get("licensing_mode"), "Unknown")}\n'
    info_text += f'MATLAB Shared With Other Notebooks: {info.get("is_shared_matlab")}\n'
    return info_text


class matlab(MATLABMagic):
    info_about_magic = f"""
    Starts a new MATLAB that is dedicated to the current kernel, instead of being shared across kernels.

    Usage: %%matlab {CMD_NEW_SESSION} or %%matlab {CMD_INFO}

    Note: To change from a shared MATLAB to a dedicated MATLAB after you have already run MATLAB code in a notebook, you must first restart the kernel.
    """
    skip_matlab_execution = False

    def before_cell_execute(self):
        """
        Processes the MATLAB magic command before cell execution.

        This method validates the parameters passed to the MATLAB magic command,
        and yields appropriate callbacks based on the command type.

        Raises:
            MagicError: If the number of parameters is not exactly one or if an unknown argument is provided.

        Yields:
            dict: A dictionary containing callback information for the kernel to process.
            The dictionary must contain a key called "type". Kernel injects itself into the callback function while
            making the call. This ensures Kernel object is available to magic instance.

        Examples: To start a new matlab session or to display information about assigned MATLAB:
                {
                    "type": "callback",
                    "callback_function": "function local to this module to be called from kernel",
                }
        """
        if len(self.parameters) != 1:
            raise MagicError(
                f"matlab magic expects only one argument. Received: {self.parameters}. Choose one of: {[arg for arg in self.get_supported_arguments()]}"
            )

        command = self.parameters[0]
        # Handles "new_session" argument
        if command == CMD_NEW_SESSION:
            yield {
                "type": "callback",
                "callback_function": handle_new_matlab_session,
            }

        # Handles "info" argument
        elif command == CMD_INFO:
            yield {
                "type": "callback",
                "callback_function": get_kernel_info,
            }

        # Handles unknown arguments
        else:
            raise MagicError(
                f"Unknown argument {command}. Choose one of: {[arg for arg in self.get_supported_arguments()]}"
            )

    def do_complete(self, parameters, parameter_pos, cursor_pos):
        """
        Provides autocompletion for the matlab magic command.

        Args:
            parameters (list): The parameters passed to the magic command
            parameter_pos (int): The position of the parameter being completed
            cursor_pos (int): The cursor position within the parameter

        Returns:
            list: A list of possible completions
        """
        matches = []
        if parameter_pos == 1:
            # Show all the arguments under matlab magic
            if cursor_pos == 0:
                matches = self.get_supported_arguments()
            # For partial input, match arguments that start with the current input
            else:
                matches = [
                    s
                    for s in self.get_supported_arguments()
                    if s.startswith(parameters[0][:cursor_pos])
                ]
        return matches

    def get_supported_arguments(self) -> list:
        """
        Returns a list of supported arguments for the MATLAB magic command.

        Returns:
            list: A list of supported arguments
        """
        return [CMD_NEW_SESSION, CMD_INFO]
