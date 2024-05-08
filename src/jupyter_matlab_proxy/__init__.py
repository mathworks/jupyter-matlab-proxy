# Copyright 2020-2024 The MathWorks, Inc.

import os
from pathlib import Path

from matlab_proxy.util.mwi import environment_variables as mwi_env
from matlab_proxy.util.mwi import token_auth as mwi_token_auth

from jupyter_matlab_proxy.jupyter_config import config


def _get_auth_token():
    """
    Generate auth token and token hash if the matlab-proxy token authentication
    is not explicitly disabled

    Returns:
        None: If token authentication is explicitly disabled
        dict: For all other cases, a token and a token_hash is returned as dictionary
    """
    mwi_enable_auth_token = os.getenv(mwi_env.get_env_name_enable_mwi_auth_token(), "")

    # Return None if token authentication is explicitly disabled
    if mwi_enable_auth_token.lower() == "false":
        return None

    # Enable token authentication by default
    original_env = os.environ.copy()
    os.environ[mwi_env.get_env_name_enable_mwi_auth_token()] = "True"
    auth_token = mwi_token_auth.generate_mwi_auth_token_and_hash()

    # Cleanup environment variables
    os.environ = original_env
    return auth_token


_mwi_auth_token = _get_auth_token()


def _get_env(port, base_url):
    """Returns a dict containing environment settings to launch the MATLAB Desktop

    Args:
        port (int): Port number on which the MATLAB Desktop will be started. Ex: 8888
        base_url (str): Controls the prefix in the url on which MATLAB Desktop will be available.
                        Ex: localhost:8888/base_url/index.html

    Returns:
        [Dict]: Containing environment settings to launch the MATLAB Desktop.
    """

    env = {
        mwi_env.get_env_name_app_port(): str(port),
        mwi_env.get_env_name_base_url(): f"{base_url}matlab",
        mwi_env.get_env_name_app_host(): "127.0.0.1",
    }

    # Add token authentication related information to the environment variables
    # dictionary passed to the matlab-proxy process if token authentication is
    # not explicitly disabled.
    if _mwi_auth_token:
        env.update(
            {
                mwi_env.get_env_name_enable_mwi_auth_token(): "True",
                mwi_env.get_env_name_mwi_auth_token(): _mwi_auth_token.get("token"),
            }
        )

    return env


def setup_matlab():
    """This method is run by jupyter-server-proxy package with instruction to launch the MATLAB Desktop

    Returns:
        [Dict]: Containing information to launch the MATLAB Desktop.
    """

    import matlab_proxy
    from matlab_proxy.constants import MWI_AUTH_TOKEN_NAME_FOR_HTTP
    from matlab_proxy.util.mwi import logger as mwi_logger

    logger = mwi_logger.get(init=True)
    logger.info("Initializing Jupyter MATLAB Proxy")

    icon_path = Path(__file__).parent / "icon_open_matlab.svg"
    logger.debug(f"Icon_path:  {icon_path}")
    logger.debug(f"Launch Command: {matlab_proxy.get_executable_name()}")
    logger.debug(f"Extension Name: {config['extension_name']}")

    jsp_config = {
        "command": [
            matlab_proxy.get_executable_name(),
            "--config",
            config["extension_name"],
        ],
        "timeout": 100,
        "environment": _get_env,
        "absolute_url": True,
        "launcher_entry": {"title": "Open MATLAB", "icon_path": icon_path},
    }

    # Add token_hash information to the request_headers_override option to
    # ensure requests from jupyter to matlab-proxy are automatically authenticated.
    # We are using token_hash instead of raw token for better security.
    if _mwi_auth_token:
        jsp_config["request_headers_override"] = {
            MWI_AUTH_TOKEN_NAME_FOR_HTTP: _mwi_auth_token.get("token_hash")
        }

    return jsp_config
