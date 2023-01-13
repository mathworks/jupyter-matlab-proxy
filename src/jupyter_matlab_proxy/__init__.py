# Copyright 2020-2021 The MathWorks, Inc.

import inspect
from pathlib import Path
from jupyter_matlab_proxy.jupyter_config import config


def _get_env(port, base_url):
    """Returns a dict containing environment settings to launch the MATLAB Desktop

    Args:
        port (int): Port number on which the MATLAB Desktop will be started. Ex: 8888
        base_url (str): Controls the prefix in the url on which MATLAB Desktop will be available.
                        Ex: localhost:8888/base_url/index.html

    Returns:
        [Dict]: Containing environment settings to launch the MATLAB Desktop.
    """
    from matlab_proxy.util.mwi import environment_variables as mwi_env

    return {
        mwi_env.get_env_name_app_port(): str(port),
        mwi_env.get_env_name_base_url(): f"{base_url}matlab",
        mwi_env.get_env_name_app_host(): "127.0.0.1",
    }


def setup_matlab():
    """This method is run by jupyter-server-proxy package with instruction to launch the MATLAB Desktop

    Returns:
        [Dict]: Containing information to launch the MATLAB Desktop.
    """

    import matlab_proxy
    from matlab_proxy.util.mwi import logger as mwi_logger

    logger = mwi_logger.get(init=True)
    logger.info("Initializing Jupyter MATLAB Proxy")

    icon_path = Path(__file__).parent / "icon_open_matlab.svg"
    logger.debug(f"Icon_path:  {icon_path}")
    logger.debug(f"Launch Command: {matlab_proxy.get_executable_name()}")
    logger.debug(f"Extension Name: {config['extension_name']}")
    return {
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
