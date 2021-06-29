# Copyright 2021 The MathWorks, Inc.
"""This file lists and exposes the environment variables which are used by the integration."""


def get_env_name_network_license_manager():
    """Specifies the path to valid license file or address of a network license server"""
    return "MLM_LICENSE_FILE"


def get_env_name_logging_level():
    """Specifies the logging level used by app's loggers"""
    return "LOG_LEVEL"


def get_env_name_log_file():
    """Specifies a file into which logging content is directed"""
    return "LOG_FILE"


def get_env_name_base_url():
    """Specifies the base url on which the website should run.
    Eg: www.127.0.0.1:8888/base_url/index.html

    Note: The website runs on a URL of the form:
        www.<SERVER ADDRESS>:<PORT NUMBER>/<BASE_URL>/index.html
    """
    return "BASE_URL"


def get_env_name_app_port():
    """Specifies the port on which the website is running on the server.
    Eg: www.127.0.0.1:PORT/index.html

    Note: The website runs on a URL of the form:
        www.<SERVER ADDRESS>:<PORT NUMBER>/<BASE_URL>/index.html
    """
    return "APP_PORT"


def get_env_name_custom_http_headers():
    """Specifies HTTP headers as JSON content, to be injected into responses sent to the browser"""
    return "CUSTOM_HTTP_HEADERS"


def get_env_name_app_host():
    """Specifies the host on which the TCP site (aiohttp server) is being run."""
    return "APP_HOST"


def get_env_name_testing():
    return "TEST"


def get_env_name_development():
    return "DEV"
