# Copyright 2024 The MathWorks, Inc.

from jupyter_matlab_kernel import mwi_logger

_logger = mwi_logger.get()


class MATLABMagic:
    """
    This class serves as the base class for all magic classes.
    Derived classes must override the following data members and methods:

    1. info_about_magic: Provides details about the magic, including but not limited to basic information, usage, limitations, and examples.
    2. skip_matlab_execution (default: False): A boolean variable that determines whether the cell should be executed in MATLAB.
    3. before_cell_execute: This function gets executed before the execution of cell in MATLAB.
    4. after_cell_execute: This function gets executed after the execution of cell in MATALB.
    5. do_complete (optional): Provides tab completion suggestions for the parameters of magics.

    Refer to the respective docstrings of these members and methods for an in-depth description.

    Args:
        parameters ([str]): The parameters passed with the magic commands.
        cell_code (str): The code contained in the cell which was executed by the user.
        magic_position_from_top (int): The execution order of the magic command from the top of the cell.
        execution_count (int): The execution count of the cell in which the magic was executed.
        line_number (int): The line number within the cell where the magic command is located.

    Example:
        For magic code execution:
            magic_object = <magic_name>(["param1", "param2"], "a = 1;\nb = 2", 1, 1)
            magic_object.before_cell_execute()
            magic_object.after_cell_execute()
        For tab completion:
            magic_object = <magic_name>()
            magic_object.do_complete(["par"], 1, 2)
    """

    info_about_magic = "No information available"
    skip_matlab_execution = False

    def __init__(
        self,
        parameters=[],
        cell_code="",
        magic_position_from_top=1,
        execution_count=1,
        line_number=1,
        logger=_logger,
    ):
        self.parameters = parameters
        self.cell_code = cell_code
        self.magic_position_from_top = magic_position_from_top
        self.execution_count = execution_count
        self.line_number = line_number
        self.logger = logger

    def before_cell_execute(self):
        """
        Gets executed before the execution of MATLAB code.

        Raises:
            MagicError: Error raised are displayed in the notebook.

        Yields:
            dict: The next output of the magic.
                The dictionary must contain a key called "type".
                For example:
                1. To display execution result:
                    {
                        "type": "execute_result",
                        "mimetype": ["text/plain", "text/html"],
                        "value": [output, f"<html><body>{output}</body></html>"],
                    }
                2. To display warnings:
                    {
                        "type": "execute_result",
                        "mimetype": ["text/html"],
                        "value": [f"<html><body><p style='color:orange;'>warning: {warning}</p></body></html>"],
                    }
                3. To modify kernel:
                    {
                        "type": "modify_kernel",
                        "murl": new_url,
                        "headers": new_headers,
                    }
            default: Empty dict ({}).
        """
        yield {}

    def after_cell_execute(self):
        """
        Gets executed after the execution of MATLAB code.

        Raises:
            MagicError: Error raised are displayed in the notebook.

        Yields:
            dict: The next output of the magic.
                The dictionary must contain a key called "type".
                For example:
                1. To display execution result:
                    {
                        "type": "execute_result",
                        "mimetype": ["text/plain", "text/html"],
                        "value": [output, f"<html><body>{output}</body></html>"],
                    }
                2. To display warnings:
                    {
                        "type": "execute_result",
                        "mimetype": ["text/html"],
                        "value": [f"<html><body><p style='color:orange;'>warning: {warning}</p></body></html>"],
                    }
                3. To modify kernel:
                    {
                        "type": "modify_kernel",
                        "murl": new_url,
                        "headers": new_headers,
                    }
            default: Empty dict ({}).
        """
        yield {}

    @classmethod
    def get_info_about_magic(cls):
        """
        Returns (string): The information about the magic to be displayed to the user.
        """
        return cls.info_about_magic

    def should_skip_matlab_execution(self):
        """
        Returns (boolean): States whether the magic blocks cell from being executed in MATLAB.
        """
        return self.skip_matlab_execution

    def do_complete(self, parameters, parameter_pos, cursor_pos):
        """
        Used to give suggestions for tab completions

        Args:
            parameters ([str]): List of parameters which were passed along with magic command.
            parameter_pos (int): The index of the parameter for which the tab completion was requested.
            cursor_pos (int): The position of the cursor in the parameter from where the tab completion was requested.

        Returns:
            [str]: An array of string containing all the possible suggestions.
        """
        return []
