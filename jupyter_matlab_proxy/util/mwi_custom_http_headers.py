# Copyright 2020-2021 The MathWorks, Inc.

import os, json, sys
from json.decoder import JSONDecodeError
from . import mwi_logger
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env

logger = mwi_logger.get()


def get():
    """Returns a dict containing custom http headers to inject into responses from the
    MATLAB Embedded Connector and to the static files in 'gui' folder.

    Parses valid JSON data if provided as a string or in a JSON file.

    Returns:
        Dict: Representing custom headers.
    """
    env_var = __get_custom_header_env_var()
    # custom_headers_path can contain valid JSON data as a string or a path to a file containing valid JSON
    custom_headers_path = os.getenv(env_var)

    # If the environment variable is not present
    if custom_headers_path is None:
        logger.info(
            f"Environment variable {env_var} is not set, hence no custom HTTP headers are applied."
        )
        return dict()

    logger.info(
        f"Envinronment variable {env_var} is set and has the value: {custom_headers_path}"
    )
    is_file = os.path.isfile(custom_headers_path)

    if is_file and __check_file_validity(custom_headers_path):
        return __get_file_contents(custom_headers_path)

    else:
        exception_statement = __get_exception_statement()
        try:
            # Valid JSON data as a string
            data = json.loads(custom_headers_path)
            logger.info(
                f"Successfully parsed HTTP headers from the environment variable {env_var}\nThe parsed HTTP headers are:\n{data}\n"
            )
            return data

        except JSONDecodeError as json_decode_error:
            # Invalid JSON data as a string.
            print(
                exception_statement.format(
                    env_var=__get_custom_header_env_var(),
                    env_var_value=custom_headers_path,
                )
            )
            logger.error(
                f"Failed with {type(json_decode_error).__name__} exception. Check the value in {env_var} environment variable for syntax errors."
            )
            sys.exit(1)

        except Exception as e:
            print(
                exception_statement.format(
                    env_var=__get_custom_header_env_var(),
                    env_var_value=custom_headers_path,
                )
            )
            logger.error(
                f"Raised {type(e).__name__} exception when parsing JSON data in the environment variable {env_var}"
            )
            sys.exit(1)


def __check_file_validity(custom_headers_path):
    """Checks the file at custom_headers_path for the read access to the file for the current python process.

    Args:
        custom_headers_path (String): File path of custom headers.

    Raises:
        OSError: When the current python process doesn't have read access to the custom_headers_path
    """
    exception_statement = __get_exception_statement()
    logger.debug(
        f"The value in environment variable {__get_custom_header_env_var()} contains a path to a file."
    )
    try:
        if not os.access(custom_headers_path, os.R_OK):
            raise OSError

        logger.debug(
            f"Current python process has read access rights to the file at: {custom_headers_path}"
        )
        return True

    except OSError as os_error:
        print(
            f"\n{type(os_error).__name__}: Permission denied. Cannot read file: {custom_headers_path}\n"
            + exception_statement.format(
                env_var=__get_custom_header_env_var(),
                env_var_value=custom_headers_path,
            )
        )
        logger.error(
            f"{type(os_error).__name__}: Permission denied. For the current python process, check read access rights for the file: {custom_headers_path}."
        )
        sys.exit(1)

    except Exception as e:
        print(
            f"\n{type(e).__name__} exception raised with error message: {e.args}\n"
            + exception_statement.format(
                env_var=__get_custom_header_env_var(),
                env_var_value=custom_headers_path,
            )
        )
        logger.error(
            f"{type(e).__name__} exception raised when checking read access rights to the file at: {custom_headers_path}"
        )
        sys.exit(1)


def __get_file_contents(custom_headers_path):
    """Reads the file containing custom headers and returns a dict.
    Raises JSONDecodeError if the JSON data in the file is not valid.

    Args:
        custom_headers_path (String): File path of custom headers.

    Raises:
        JSONDecodeError: when the contents of the file containing custom headers
        does not have valid JSON data.

    Returns:
        Dict: Containing custom headers.
    """

    custom_headers = None
    exception_statement = __get_exception_statement()
    try:
        with open(custom_headers_path, "r") as json_file:
            custom_headers = json.load(json_file)
            logger.info(
                f"Successfully parsed HTTP headers present in the file: {custom_headers_path}"
            )
            logger.debug(f"The parsed HTTP headers are :\n{custom_headers}\n")
            return custom_headers

    except JSONDecodeError as json_decode_error:
        print(
            f"\n{type(json_decode_error).__name__} exception raised with error message: {json_decode_error.args[0]}\n"
            + exception_statement.format(
                env_var=__get_custom_header_env_var(),
                env_var_value=custom_headers_path,
            )
        )
        logger.error(
            f"{type(json_decode_error).__name__}: Failed to parse JSON data in the file: {custom_headers_path}.\nCheck contents of the file for any syntax errors."
        )
        sys.exit(1)

    except Exception as e:
        print(
            f"\nFailed with {type(e).__name__} exception with error message:\n{e.args}"
            + exception_statement.format(
                env_var=__get_custom_header_env_var(),
                env_var_value=custom_headers_path,
            )
        )
        logger.error(
            f"Failed with {type(e).__name__}  when reading JSON data from the file: {custom_headers_path}"
        )
        sys.exit(1)


def __get_custom_header_env_var():
    """Returns the name of the environment variable which contains path
    to the file containing custom headers.

    Returns:
        String: Environment variable containing path to the file containing custom headers.
    """
    return mwi_env.get_env_name_custom_http_headers()


def __get_exception_statement():
    """Returns a generic exception statement pertaining to HTTP headers.

    Returns:
        String: Containing a generic exception statement to print to stdout.
    """
    exception_statement = """HTTP headers defined in the environment variable {env_var} are not valid.\n
    The value in {env_var} is: {env_var_value}\n
    Please provide either valid JSON data as a string or a path to a file with read access containing valid JSON data."""

    return exception_statement
