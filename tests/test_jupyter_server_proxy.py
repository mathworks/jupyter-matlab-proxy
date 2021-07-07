# Copyright 2020-2021 The MathWorks, Inc.

import jupyter_matlab_proxy
import os
from pathlib import Path
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env


def test_get_env():
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
    port = 10000
    base_url = "/foo/"
    icon_path = str(
        os.path.join(Path(os.getcwd()), "jupyter_matlab_proxy", "icons", "matlab.svg")
    )

    expected_matlab_setup = {
        "command": ["matlab-jupyter-app"],
        "timeout": 100,
        "environment": jupyter_matlab_proxy._get_env(port, base_url),
        "absolute_url": True,
        "launcher_entry": {
            "title": "MATLAB",
            "icon_path": icon_path,
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    actual_matlab_setup["environment"] = actual_matlab_setup["environment"](
        port, base_url
    )

    assert expected_matlab_setup == actual_matlab_setup
