# Copyright 2024 The MathWorks, Inc.
# Helper functions to access & control the logging behavior of the app

import logging
import os


def get(init=False):
    """Get the logger used by this application.
        Set init=True to initialize the logger
    Returns:
        Logger: The logger used by this application.
    """
    if init is True:
        return __set_logging_configuration()

    return __get_mw_logger()


def __get_mw_logger_name():
    """Name of logger used by the app

    Returns:
        String: The name of the Logger.
    """
    return "MATLABKernel"


def __get_mw_logger():
    """Returns logger for use in this app.

    Returns:
        Logger: A logger object
    """
    return logging.getLogger(__get_mw_logger_name())


def __set_logging_configuration():
    """Sets the logging environment for the app

    Returns:
        Logger: Logger object with the set configuration.
    """
    # query for user specified environment variables
    log_level = os.getenv(__get_env_name_logging_level(), __get_default_log_level())

    ## Set logging object
    logger = __get_mw_logger()

    # log_level is either set by environment or is the default value.
    logger.info(f"Initializing logger with log_level: {log_level}")
    logger.setLevel(log_level)

    # Allow other libraries used by this integration to
    # also print their logs at the specified level
    logging.basicConfig(level=log_level)

    return logger


def __get_env_name_logging_level():
    """Specifies the logging level used by app's loggers"""
    return "MWI_JUPYTER_LOG_LEVEL"


def __get_default_log_level():
    """The default logging level used by this application.

    Returns:
        String: The default logging level
    """
    return "INFO"
