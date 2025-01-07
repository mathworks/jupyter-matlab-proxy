# Copyright 2020-2025 The MathWorks, Inc.

import os
import secrets
from pathlib import Path

import matlab_proxy
from matlab_proxy.constants import MWI_AUTH_TOKEN_NAME_FOR_HTTP
from matlab_proxy.util.mwi import environment_variables as mwi_env
from matlab_proxy.util.mwi import logger as mwi_logger
from matlab_proxy.util.mwi import token_auth as mwi_token_auth

from jupyter_matlab_proxy.jupyter_config import config

_MPM_AUTH_TOKEN: str = secrets.token_hex(32)
_JUPYTER_SERVER_PID: str = str(os.getpid())
_USE_FALLBACK_KERNEL: bool = (
    os.getenv("MWI_USE_FALLBACK_KERNEL", "FALSE").lower().strip() == "true"
)


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
    env = {}
    if _USE_FALLBACK_KERNEL:
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

    else:
        # case when we are using matlab proxy manager
        import matlab_proxy_manager.utils.environment_variables as mpm_env

        env = {
            mpm_env.get_env_name_mwi_mpm_port(): str(port),
            mpm_env.get_env_name_mwi_mpm_auth_token(): _MPM_AUTH_TOKEN,
            mpm_env.get_env_name_mwi_mpm_parent_pid(): _JUPYTER_SERVER_PID,
        }
    return env


def setup_matlab():
    """This method is run by jupyter-server-proxy package with instruction to launch the MATLAB Desktop

    Returns:
        [Dict]: Containing information to launch the MATLAB Desktop.
    """

    logger = mwi_logger.get(init=True)
    logger.info("Initializing Jupyter MATLAB Proxy")

    jsp_config = _get_jsp_config(logger=logger)

    return jsp_config


def _get_jsp_config(logger):
    icon_path = Path(__file__).parent / "icon_open_matlab.svg"
    logger.debug("Icon_path: %s", icon_path)
    jsp_config = {}

    if _USE_FALLBACK_KERNEL:
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
        logger.debug("Launch Command: %s", jsp_config.get("command"))

        # Add token_hash information to the request_headers_override option to
        # ensure requests from jupyter to matlab-proxy are automatically authenticated.
        # We are using token_hash instead of raw token for better security.
        if _mwi_auth_token:
            jsp_config["request_headers_override"] = {
                MWI_AUTH_TOKEN_NAME_FOR_HTTP: _mwi_auth_token.get("token_hash")
            }
    else:
        import matlab_proxy_manager
        from matlab_proxy_manager.utils import constants

        # JSP config for when we are using matlab proxy manager
        jsp_config = {
            # Starts proxy manager process which in turn starts a shared matlab proxy instance
            # if not already started. This gets invoked on clicking `Open MATLAB` button and would
            # always take the user to the default (shared) matlab-proxy instance.
            "command": [matlab_proxy_manager.get_executable_name()],
            "timeout": 100,  # timeout in seconds
            "environment": _get_env,
            "absolute_url": True,
            "launcher_entry": {"title": "Open MATLAB", "icon_path": icon_path},
        }
        logger.debug("Launch Command: %s", jsp_config.get("command"))

        # Add jupyter server pid and mpm_auth_token to the request headers for resource
        # filtering and Jupyter to proxy manager authentication
        jsp_config["request_headers_override"] = {
            constants.HEADER_MWI_MPM_CONTEXT: _JUPYTER_SERVER_PID,
            constants.HEADER_MWI_MPM_AUTH_TOKEN: _MPM_AUTH_TOKEN,
        }

    return jsp_config
