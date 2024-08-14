# Copyright 2024 The MathWorks, Inc.

import importlib
import re

from jupyter_matlab_kernel import mwi_logger
from jupyter_matlab_kernel.magic_helper import get_magic_names
from jupyter_matlab_kernel.mwi_exceptions import MagicError, MagicExecutionEngineError

_logger = mwi_logger.get()


def get_magics_for_execution(magics, cell_code, execution_count, logger=_logger):
    """
    Locates the magic class and initializes them by creating the object for the respective classes.

    Args:
        magics (List[dict]): A list of magic dictionary having keys "name" and "params".
        cell_code (str): The code in the cell.
        execution_count (int): The position at which the cell was executed.

    Returns:
        magics_for_execution (List([class object])): object of all the given `magics`.
    """
    magics_for_execution = []
    if not isinstance(magics, list):
        logger.error(
            f"Expected a list of magic dictionary got a {type(magics)} instead."
        )
        raise TypeError("Error occured during the initialization of Magic commands.")
    for index, magic in enumerate(magics):
        try:
            magic_class = get_magic_class(magic["name"])
            logger.debug(f"The name of magic is {magic['name']}")
            magics_for_execution.append(
                instantiate_magic(
                    magic_class,
                    magic["params"],
                    cell_code,
                    index + 1,
                    execution_count,
                    magic["line_number"],
                    logger,
                )
            )
        except AttributeError:
            error_message = f"The magic '{magic['name']}' does not have a class named '{magic['name']}'."
            raise MagicExecutionEngineError(error_message)
        except ModuleNotFoundError:
            error_message = f"The magic '{magic['name']}' does not exist."
            raise MagicExecutionEngineError(error_message)
        except Exception as e:
            error_message = f"Error occured while locating and initializing magics: {e}"
            raise MagicExecutionEngineError(error_message)
    return magics_for_execution


def instantiate_magic(
    magic_class,
    magic_parameters,
    cell_code,
    magic_position,
    execution_count,
    line_number,
    logger=_logger,
):
    """
    Initializes the magic classes and stores the object in magics_for_execution.

    Args:
        magic_class (class): The class of the magic.
        magic_parameters ([str]): Parameters which are to be passed to the magic classes.
        cell_code (str): The code in the cell.
        magic_position (int): The position of the magic with respect to other magics in the same cell.
        execution_count (int): The position at which the cell was executed.

    Returns:
        initialized_magic_object (class object): initialized object of the given magic class.
    """

    initialized_magic_object = magic_class(
        magic_parameters,
        cell_code,
        magic_position,
        execution_count,
        line_number,
        logger,
    )
    return initialized_magic_object


def get_magic_class(magic_name, logger=_logger):
    """
    Locates the magic class

    Args:
        magic_name (str): name of the magic class

    Returns:
        class: The class of the magic_name

    Raises:
        ModuleNotFoundError: When the magic file does not exist.
        AttributeError: When the magic file exists but it does not contain a class with <magic_name>
    """
    if not MagicExecutionEngine.get_magic_module(magic_name):
        path_of_magic_in_module = f"jupyter_matlab_kernel.magics.{magic_name}"
        magic_module = importlib.import_module(path_of_magic_in_module)
        MagicExecutionEngine.set_magic_module(magic_name, magic_module)
        logger.debug(
            f"The magic {magic_name} was not found initializing and adding it to imported_magic_module"
        )
    return getattr(MagicExecutionEngine.get_magic_module(magic_name), magic_name)


def get_magics_from_cell(cell_code):
    """
    Extracts magic commands from the cell_code

    Args:
        cell_code (str): The code in the cell.

    Returns:
        List[dict]: A list of magics in cell_code.
            Example dictionary:
            {
                "name": "help",
                "params": ["file"],
                "line_number": 1,
            }
        matlab_starts_from_line_number (int): The line in the cell from which MATLAB code starts. None if no MATLAB code

    """
    lines = cell_code.split("\n")
    magics = []
    line_number = 0
    matlab_starts_from_line_number = None
    for line in lines:
        # Whitespaces before the magic commands are accepted. Consistent with Ipython's magic
        line = line.strip()
        line_number += 1
        magic_matches = re.match(r"%%(?P<name>\w+)(?P<params>.*)", line)
        if magic_matches:
            magic_dict = magic_matches.groupdict()
            params = magic_dict["params"].strip()
            if params:
                magic_dict["params"] = re.split("\s+", params)
            else:
                magic_dict["params"] = []
            magic_dict["line_number"] = line_number
            magics.append(magic_dict)
        elif line:
            # Stop processing any magic commands after encountering a MATLAB code in the cell.
            # If any magics are defined after MATLAB code, then they are simply treated as comments.
            # This is done to improve the performance, reduce complexity, as well to ensure that even
            # if a notebook was created from lets say a MLX file using a converter, it will not error out.
            matlab_starts_from_line_number = line_number
            break
    return magics, matlab_starts_from_line_number


def magic_executor(magics_for_execution, magic_execution_function):
    """
    Used to execute a specific function from the magics extracted from cell_code.

    Args:
        magics_for_execution ([class object]): A list of magic objects
        magic_execution_function (str): The name of the function to be executed from magic class.

    Yields:
        output_from_methods ([any]): The output obtained after executing the method from the magic class.
    """
    for magic_for_execution in magics_for_execution:
        try:
            magic_method = getattr(magic_for_execution, magic_execution_function)
            for output_from_method in magic_method():
                if output_from_method:
                    if "type" in output_from_method:
                        yield output_from_method
                    else:
                        raise MagicError(
                            f"Invalid result returned by a Magic command. Contact Magic Author to fix. \n Error: {output_from_method}\n Does not contain a key called type."
                        )
        except MagicError as e:
            raise MagicExecutionEngineError(
                f"Error using {magic_for_execution.__class__.__name__} magic: \n{e}"
            )
        except Exception as e:
            raise MagicExecutionEngineError(f"Magic execution error: {e}")


def should_skip_matlab_execution(magics):
    """
    Determines whether the magics blocks cell from being executed in MATLAB.
    MATLAB execution will be skipped if any of the magics in a cell states that matlab execution must be skipped.
    Args:
        magics ([class object]): A List of Magic object

    Returns:
        bool: Whether the magic blocks MATLAB execution.
    """
    should_skip_matlab_execution = False
    for magic in magics:
        should_skip_matlab_execution |= magic.should_skip_matlab_execution()
    return should_skip_matlab_execution


def get_completion_result_for_magics(cell_code, cursor_pos, logger=_logger):
    """
    For tab completion gives the tab completion suggestions for magic and magic parameters.

    Args:
        cell_code (str): The code in the cell.
        cursor_pos (int): The position of the cursor in the cell_code.

    Returns:
        None: if it is not a magic command.
        {
            "matches": matches,
            "start": start,
            "end": end,
            "completions": {
                "text": match,
                "type": "magic",
                "start": start,
                "end": end
            },...
        }
    """
    cursor_at_line_number, cursor_pos_relative_to_line = find_cursor_line(
        cell_code, cursor_pos
    )

    magics, matlab_code_starts_from_line_number = get_magics_from_cell(cell_code)

    # Tab completion for magics will only work if declared before MATLAB code.
    if (matlab_code_starts_from_line_number is None) or (
        cursor_at_line_number <= matlab_code_starts_from_line_number
    ):
        matches, cursor_pos_relative_to_word = get_completion_matches(
            cell_code,
            magics,
            cursor_at_line_number,
            cursor_pos_relative_to_line,
            logger,
        )

        if matches is None:
            return None
        logger.debug(f"Matching array {matches}")
        completion_response = create_completion_response(
            matches, cursor_pos, cursor_pos_relative_to_word
        )
        return completion_response

    else:
        logger.debug("Not a magic syntax")
        return None


def get_completion_matches(
    cell_code,
    magics,
    cursor_at_line_number,
    cursor_pos_relative_to_line,
    logger=_logger,
):
    """
    For tab completion gives the possible matches for magic commands

    Args:
        cell_code (str): The code in the cell.
        magics (List[dict]): A list of magics in cell_code.
        cursor_at_line_number (int): The line number at which the cursor is positioned.
        cursor_pos_relative_to_line (int): The position of the cursor relative to the line.

    Returns:
        matches (List[str]): The possible matches for tab completion.
        cursor_pos_relative_to_word (int): The position of the cursor relative to the word.
    """
    formatted_cell_code = cell_code.split("\n")
    # The line numbers of the cell starts from 1 while the indexing starts from 0.
    # Subtracting 1 from the line number to get the correct line of code.
    line_code_at_cursor_pos = formatted_cell_code[cursor_at_line_number - 1]
    cursor_is_on_word_number, cursor_pos_relative_to_word = find_cursor_word(
        line_code_at_cursor_pos, cursor_pos_relative_to_line
    )

    matches = []
    is_cursor_line_in_magics = False
    for magic in magics:
        if cursor_at_line_number == magic["line_number"]:
            matches, cursor_pos_relative_to_word = get_completion_matches_from_magic(
                magic,
                cursor_is_on_word_number,
                cursor_pos_relative_to_word,
                logger,
            )
            is_cursor_line_in_magics = True
            break

    if not is_cursor_line_in_magics:
        matches, cursor_pos_relative_to_word = get_completion_matches_for_magic_names(
            line_code_at_cursor_pos,
            cursor_is_on_word_number,
            cursor_pos_relative_to_word,
            logger,
        )
    return matches, cursor_pos_relative_to_word


def get_completion_matches_from_magic(
    magic,
    cursor_is_on_word_number,
    cursor_pos,
    logger=_logger,
):
    """
    For tab completion gives the possible matches for magic parameters and magic names

    Args:
        magic (dict): Contains magic name and parameters.
        cursor_is_on_word_number (int): The word at which the cursor is at.
        cursor_pos (int): The position of the cursor relative to the word.

    Returns:
        matches (List[str]): The possible matches for tab completion.
        cursor_pos (int): The position of the cursor relative to the word.
    """
    logger.debug(
        f"The cursor is on word {cursor_is_on_word_number} and magic dictionary is {magic} cursors relative position relative to word is: {cursor_pos}"
    )
    if cursor_is_on_word_number == 1:
        matches = [
            s
            for s in get_magic_names()
            if s.startswith(magic["name"][: cursor_pos - 2])
        ]
        # Subtracting 2 to later compute the correct values for `start` and `end` to ignore %% from the syntax during tab completion
        cursor_pos -= 2
    else:
        logger.debug("Tab completion requested from the magic")
        matches = get_completion_matches_for_magic_parameters(
            magic["name"],
            magic["params"],
            cursor_is_on_word_number - 1,
            cursor_pos,
            logger,
        )
    return matches, cursor_pos


def get_completion_matches_for_magic_parameters(
    magic_name,
    magic_params,
    param_position,
    cursor_pos,
    logger=_logger,
):
    """
    For tab completion gives the possible matches for magic parameters.

    Args:
        magic_name (str): The name of the magic
        magic_params (List[str]): The list of parameters passed for magics
        param_position (int): The param at which the cursor is at.
        cursor_pos (int): The position of the cursor relative to the parameter.

    Returns:
        matches (List[str]): The possible matches for tab completion.
    """
    try:
        magic_class = get_magic_class(magic_name)
        magic_object_for_tab_completion = magic_class()
        matches = magic_object_for_tab_completion.do_complete(
            magic_params,
            param_position,
            cursor_pos,
        )
    except Exception as e:
        logger.error(f"Tab completion failed with error message {e}")
        matches = []
    return matches


def get_completion_matches_for_magic_names(
    line_code_at_cursor_pos,
    cursor_is_on_word_number,
    cursor_pos_relative_to_word,
    logger=_logger,
):
    """
    For tab completion gives the possible matches when the cursor is placed right after double percentages.

    Args:
        line_code_at_cursor_pos (int): The line of code at the position where cursor is at.
        cursor_is_on_word_number (int): The word at which the cursor position is at.
        cursor_pos_relative_to_word (int): The position of the cursor relative to the word.

    Returns:
        matches (List[str]): The possible matches for tab completion.
        cursor_pos_relative_to_word (int): The position of the cursor relative to the word.
    """
    formatted_line_code = line_code_at_cursor_pos.strip()
    if formatted_line_code.startswith("%%"):

        if cursor_is_on_word_number == 1 and cursor_pos_relative_to_word == 2:
            # When the cursor position is right after %%.
            matches = get_magic_names()
            # Subtracting 2 to later compute the correct values for `start` and `end` to ignore %% from the syntax during tab completion
            cursor_pos_relative_to_word -= 2
        else:
            logger.debug("Starts with %% but not a valid magic syntax")
            matches = None
    else:
        logger.debug("Not a magic syntax because line does not starts with %%")
        matches = None
    return matches, cursor_pos_relative_to_word


def create_completion_response(matches, cursor_pos, cursor_pos_relative_to_word):
    """
    Creates a response for tab completion

    Args:
        matches (List[str]): A list of possible matches for tab completion
        cursor_pos (int): The cursor position relative to the whole cell.
        cursor_pos_relative_to_word (int): The position of the cursor relative to the word.

    Returns:
        {
            "matches": matches,
            "start": start,
            "end": end,
            "completions": {
                "text": match,
                "type": "magic",
                "start": start,
                "end": end
            },...
        }
    """
    start = cursor_pos - cursor_pos_relative_to_word
    end = cursor_pos
    return {
        "matches": matches,
        "start": start,
        "end": end,
        "completions": [
            {"text": match, "type": "magic", "start": start, "end": end}
            for match in matches
        ],
    }


def find_cursor_line(cell_code, cursor_pos):
    """
    Finds the line number of the cursor position and number of letters in that line before the cursor.

    Args:
        cell_code (str): The code in the cell.
        cursor_pos (int): The position of the cursor with respect to the cell_code.

    Returns:
        line_number (int): The line number at the position of the cursor.
        cursor_pos_relative_to_line (int): The number of letters before the cursor with respect to the line.
    """
    line_number = 1
    current_pos = 0
    cursor_pos_relative_to_line = 0
    while cursor_pos != current_pos:
        cursor_pos_relative_to_line = cursor_pos_relative_to_line + 1
        # When next line character is encountered increase the line number and reset relative cursor position.
        if cell_code[current_pos] == "\n":
            cursor_pos_relative_to_line = 0
            line_number = line_number + 1
        current_pos = current_pos + 1
    return line_number, cursor_pos_relative_to_line


def find_cursor_word(line_code, cursor_pos):
    """
    Finds the word number of the cursor position and number of letters in the word before the cursor.

    Args:
        line_code (str): A single line of code.
        cursor_pos (int): The position of the cursor with respect to the line_code.

    Returns:
        word_number (int): The word number at the position of the cursor.
        cursor_pos_relative_to_word (int): The number of letters before the cursor with respect to the word.
    """
    word_number = 0
    current_pos = 0
    cursor_pos_relative_to_word = 0
    previous_letter = " "
    while current_pos < cursor_pos:
        # Consecutive whitespaces are not treated as words.
        if previous_letter == " " and line_code[current_pos] != " ":
            word_number = word_number + 1

        # If a whitespace is encountered. Then reset the value of relative cursor position
        if line_code[current_pos] == " ":
            cursor_pos_relative_to_word = 0
        else:
            cursor_pos_relative_to_word = cursor_pos_relative_to_word + 1

        previous_letter = line_code[current_pos]
        current_pos = current_pos + 1
    # if there was a whitespace at the last location then current cursor position is the start of a new word.
    if previous_letter == " ":
        word_number = word_number + 1
    return word_number, cursor_pos_relative_to_word


class MagicExecutionEngine:
    """
    This class is responsible for the parsing, mapping, execution and tab completion of magic commands.
    """

    # Dictionary to store magic modules as key-value pairs: {<magic_name>: <imported_magic_module>}
    # This dictionary populates itself when magics are executed from the kernel
    # to prevent repeated lookups of modules in the file system.
    # The lifetime of this dictionary is the same as the lifetime of the kernel.
    imported_magic_modules = {}

    @classmethod
    def pre_load_magic_modules(cls):
        magic_names = get_magic_names()
        for magic_name in magic_names:
            path_of_magic_in_module = f"jupyter_matlab_kernel.magics.{magic_name}"
            cls.imported_magic_modules[magic_name] = importlib.import_module(
                path_of_magic_in_module
            )

    @classmethod
    def get_magic_module(cls, magic_name):
        return cls.imported_magic_modules.get(magic_name)

    @classmethod
    def set_magic_module(cls, magic_name, magic_module):
        cls.imported_magic_modules[magic_name] = magic_module

    def __init__(self, logger=_logger):
        self.logger = logger
        MagicExecutionEngine.pre_load_magic_modules()

    def process_before_cell_execution(self, cell_code, execution_count):
        """
        Executes the before_cell_execute function of the magics present in cell_code

        Args:
            cell_code (str): The code in the cell.
            execution_count (int): The position at which the cell was executed.
        """
        # A list of magic class instances to be executed in the cell.
        self.magics_for_execution = []
        # Line number in a cell starts from 1, None means that the cell does not contains MATLAB code.
        self.matlab_starts_from_line_number = None
        # Indicates if the magics in the cell want to skip cell from being executd in  MATLAB.
        self.skip_matlab_execution = False
        try:
            magics, self.matlab_starts_from_line_number = get_magics_from_cell(
                cell_code
            )
            if magics:
                self.magics_for_execution = get_magics_for_execution(
                    magics, cell_code, execution_count, self.logger
                )

                self.skip_matlab_execution = should_skip_matlab_execution(
                    self.magics_for_execution
                )

                for output in magic_executor(
                    self.magics_for_execution, "before_cell_execute"
                ):
                    yield (output)

        except Exception as e:
            raise MagicExecutionEngineError(e)

    def process_after_cell_execution(self):
        """
        Executes the after_cell_execute function of the magics present in cell_code. Takes no args.
        """
        try:
            # Reversing so that first magic is exited last
            self.magics_for_execution.reverse()
            for output in magic_executor(
                self.magics_for_execution, "after_cell_execute"
            ):
                yield (output)

        except Exception as e:
            raise MagicExecutionEngineError(e)

    def skip_cell_execution(self):
        """
        Determine whether the current cell should be executed in MATLAB.

        This function checks if the cell execution should be skipped based on
        two conditions:

            1. If MATLAB execution is skipped by any of the magic commands (`self.skip_matlab_execution`).
            2. If the current cell contains MATLAB code (`self.matlab_starts_from_line_number`).

        Returns:
            bool: True if the matlab execution should be skipped, False otherwise.
        """
        return self.skip_matlab_execution or (
            self.matlab_starts_from_line_number is None
        )
