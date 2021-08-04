# Copyright 2021 The MathWorks, Inc.
"""This file lists and exposes the environment variables which are used by the integration."""

import os


def get_env_name_network_license_manager():
    """Specifies the path to valid license file or address of a network license server"""
    return "MLM_LICENSE_FILE"


def get_env_name_mhlm_context():
    """Specifies the context from which MHLM was initiated. Used by DDUX in MATLAB."""
    return "MHLM_CONTEXT"


def get_env_name_logging_level():
    """Specifies the logging level used by app's loggers"""
    return "MWI_LOG_LEVEL"


def get_env_name_web_logging_enabled():
    """Enable the logging of asyncio web traffic by setting to true"""
    return "MWI_WEB_LOGGING_ENABLED"


def get_env_name_log_file():
    """Specifies a file into which logging content is directed"""
    return "MWI_LOG_FILE"


def get_env_name_base_url():
    """Specifies the base url on which the website should run.
    Eg: www.127.0.0.1:8888/base_url/index.html

    Note: The website runs on a URL of the form:
        www.<SERVER ADDRESS>:<PORT NUMBER>/<BASE_URL>/index.html

    Note: If you are updating this value, remember to update the startup.m file
            that is used to notify the connector of the base url.
    """
    return "MWI_BASE_URL"


def get_env_name_app_port():
    """Specifies the port on which the website is running on the server.
    Eg: www.127.0.0.1:PORT/index.html

    Note: The website runs on a URL of the form:
        www.<SERVER ADDRESS>:<PORT NUMBER>/<BASE_URL>/index.html
    """
    return "MWI_APP_PORT"


def get_env_name_custom_http_headers():
    """Specifies HTTP headers as JSON content, to be injected into responses sent to the browser"""
    return "MWI_CUSTOM_HTTP_HEADERS"


def get_env_name_app_host():
    """Specifies the host on which the TCP site (aiohttp server) is being run."""
    return "MWI_APP_HOST"


def get_env_name_testing():
    """Set to true when we are running tests in development mode."""
    return "MWI_TEST"


def get_env_name_development():
    """Set to true when we are in development mode."""
    return "MWI_DEV"


def is_development_mode_enabled():
    """Returns true if the app is in development mode."""
    return os.environ.get(get_env_name_development(), "false").lower() == "true"


def is_testing_mode_enabled():
    """Returns true if the app is in testing mode."""
    return (
        is_development_mode_enabled()
        and os.environ.get(get_env_name_testing(), "false").lower() == "true"
    )


def is_web_logging_enabled():
    """Returns true if the web logging is required to be enabled"""
    return os.environ.get(get_env_name_web_logging_enabled(), "false").lower() == "true"
