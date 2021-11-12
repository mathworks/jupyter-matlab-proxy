# Copyright 2020-2021 The MathWorks, Inc.

import os, inspect
import matlab_proxy, jupyter_matlab_proxy
from pathlib import Path
from matlab_proxy import mwi_environment_variables as mwi_env
from jupyter_matlab_proxy.jupyter_config import config


def test_get_env():
    """Tests if _get_env() method returns the expected enviroment settings as a dict."""

    port = 10000
    base_url = "/foo/"
    r = jupyter_matlab_proxy._get_env(port, base_url)
    assert r[mwi_env.get_env_name_app_port()] == str(port)
    assert r[mwi_env.get_env_name_base_url()] == f"{base_url}matlab"


def test_setup_matlab():
    """Tests for a valid Server Process Configuration Dictionary

    This test checks if the jupyter proxy returns the expected Server Process Configuration
    Dictionary for the Matlab process.
    """
    # Setup
    package_path = Path(inspect.getfile(matlab_proxy)).parent
    icon_path = package_path / "icons" / "matlab.svg"

    expected_matlab_setup = {
        "command": [
            matlab_proxy.get_executable_name(),
            "--config",
            config["extension_name"],
        ],
        "timeout": 100,
        "environment": jupyter_matlab_proxy._get_env,
        "absolute_url": True,
        "launcher_entry": {
            "title": "MATLAB",
            "icon_path": icon_path,
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    assert expected_matlab_setup == actual_matlab_setup
    assert os.path.isfile(actual_matlab_setup["launcher_entry"]["icon_path"])
