# Copyright 2020-2021 The MathWorks, Inc.
"""This file contains validators for various runtime artefacts.
A validator is defined as a function which verifies the input and 
returns it unchanged if validation passes. 
Returning inputs allows validators to be used inline with the input.

Example: 
Original code: if( input ):
With validator: if (valid(input)):

Exceptions are thrown to signal failure.
"""
from . import mwi_logger
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
import sys

logger = mwi_logger.get()


def validate_mlm_license_file(nlm_conn_str):
    """Validates and returns input if it passes validation.
    Throws exception when validation fails.
    The connection string should be in the form of port@hostname
    OR path to valid license file
    """
    import re
    import os
    from .mwi_exceptions import NetworkLicensingError

    if nlm_conn_str is None:
        return None

    # TODO: The JS validation of this setting does not allow file path locations
    # The JS validation occurs before reaching the set_licensing_info endpoint.

    # Regular expression to match port@hostname,
    # where port is any number and hostname is alphanumeric
    # regex = Start of Line, Any number of 0-9 digits , @, any number of nonwhite space characters with "- _ ." allowed
    # "^[0-9]+[@](\w|\_|\-|\.)+$"
    # Server triad is of the form : port@host1,port@host2,port@host3
    regex = "(^[0-9]+[@](\w|\_|\-|\.)+$)|(^[0-9]+[@](\w|\_|\-|\.)+),([0-9]+[@](\w|\_|\-|\.)+),([0-9]+[@](\w|\_|\-|\.)+$)"
    if not re.search(regex, nlm_conn_str):
        logger.debug("NLM info is not in the form of port@hostname")
        if not os.path.isfile(nlm_conn_str):
            logger.debug("NLM info is not a valid path to a license file")
            error_message = (
                f"MLM_LICENSE_FILE validation failed for {nlm_conn_str}. "
                f"If set, the MLM_LICENSE_FILE environment variable must be a string which is either of the form port@hostname"
                f" OR path to a valid license file."
            )
            logger.error(error_message)
            raise NetworkLicensingError(error_message)
        else:
            logger.info(
                f"MLM_LICENSE_FILE with value: {nlm_conn_str} is a path to a file. MATLAB will attempt to use it."
            )
    else:
        logger.info(
            f"MLM_LICENSE_FILE with value: {nlm_conn_str} is a license server, MATLAB will attempt to connect to it."
        )

    # Validation passed
    return nlm_conn_str


def validate_app_port_is_free(port):
    """Validates and returns port if its free else will error out and exit.

    Args:
        port (str|int): Port number either as a string or an integer.

    Raises:
        e: socket.error

    Returns:
        Boolean: True if provided port is occupied else False.
    """
    import socket, errno

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", int(port)))
        s.close()

        # Was able to allocate port. Validation passed.
        return port
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            logger.error(
                f"The port {port} is not available. Please set another value for the environment variable {mwi_env.get_env_name_app_port()}"
            )
            sys.exit(1)
        else:
            raise e
