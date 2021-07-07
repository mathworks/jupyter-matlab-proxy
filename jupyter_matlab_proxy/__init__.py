# Copyright 2020-2021 The MathWorks, Inc.

import os
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env


def _get_env(port, base_url):
    return {
        mwi_env.get_env_name_app_port(): str(port),
        mwi_env.get_env_name_base_url(): f"{base_url}matlab",
        mwi_env.get_env_name_app_host(): "127.0.0.1",
        mwi_env.get_env_name_mhlm_context(): "MATLAB_JUPYTER",
    }


def setup_matlab():
    return {
        "command": ["matlab-jupyter-app"],
        "timeout": 100,
        "environment": _get_env,
        "absolute_url": True,
        "launcher_entry": {
            "title": "MATLAB",
            "icon_path": os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "icons", "matlab.svg"
            ),
        },
    }
