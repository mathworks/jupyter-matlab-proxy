# Copyright 2020-2021 The MathWorks, Inc.

import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import uuid
import shutil


def get_matlab_path():
    which_matlab = shutil.which("matlab")
    if which_matlab is None:
        return None
    return Path(which_matlab).resolve().parent.parent


def get_matlab_version(matlab_path):
    """Get the MATLAB Release version in this image"""

    if matlab_path is None:
        return None

    tree = ET.parse(matlab_path / "VersionInfo.xml")
    root = tree.getroot()
    return root.find("release").text


def get_ws_env_settings():
    ws_env = (os.getenv("WS_ENV") or "").lower()
    ws_env_suffix = f"-{ws_env}" if "integ" in ws_env else ""

    return ws_env, ws_env_suffix


def get_dev_settings():
    devel_file = Path(__file__).resolve().parent / "./devel.py"
    matlab_ready_file = Path(tempfile.mkstemp()[1])
    ws_env, ws_env_suffix = get_ws_env_settings()

    return {
        "matlab_path": Path(),
        "matlab_version": "R2020b",
        "matlab_cmd": [
            "python",
            "-u",
            str(devel_file),
            "matlab",
            "--ready-file",
            str(matlab_ready_file),
        ],
        "xvfb_cmd": [
            "python",
            "-u",
            str(devel_file),
            "xvfb",
            "--ready-file",
            str(Path(tempfile.gettempdir()) / ".X11-unix" / "X1"),
        ],
        "matlab_ready_file": matlab_ready_file,
        "base_url": os.environ.get("BASE_URL", ""),
        "app_port": os.environ.get("APP_PORT", 8000),
        "host_interface": os.environ.get("APP_HOST", "127.0.0.1"),
        "mwapikey": str(uuid.uuid4()),
        "matlab_protocol": "http",
        "matlab_display": ":1",
        "nlm_conn_str": os.environ.get("MLM_LICENSE_FILE"),
        "matlab_config_file": Path(tempfile.gettempdir())
        / ".matlab"
        / "proxy_app_config.json",
        "ws_env": ws_env,
        "mwa_api_endpoint": f"https://login{ws_env_suffix}.mathworks.com/authenticationws/service/v4",
        "mhlm_api_endpoint": f"https://licensing{ws_env_suffix}.mathworks.com/mls/service/v1/entitlement/list",
        "mwa_login": f"https://login{ws_env_suffix}.mathworks.com",
    }


def get(dev=False):
    """Method which returns the settings specific to the environment in which the server is running in
    If the environment variable 'TEST' is set  to true, will make some changes to the dev settings.

    Args:
        dev (bool, optional): development environment. Defaults to False.

    Returns:
        Dict: Containing data on how to start MATLAB among other information.
    """

    if dev:
        settings = get_dev_settings()

        # If running tests using Pytest, it will set environment variable TEST to true before running tests.
        # Will make test env specific changes before returning the settings.
        if os.environ.get("TEST", "False").lower() == "true":

            # Set ready_delay value to 0 for faster fake MATLAB startup.
            ready_delay = ["--ready-delay", "0"]
            matlab_cmd = settings["matlab_cmd"]
            matlab_cmd[4:4] = ready_delay
            settings["matlab_cmd"] = matlab_cmd

            # Set NLM Connection string. Server will start using this connection string for licensing
            settings["nlm_conn_str"] = "abc@nlm"

        return settings

    else:
        matlab_startup_file = str(
            Path(__file__).resolve().parent / "matlab" / "startup.m"
        )
        matlab_path = get_matlab_path()
        ws_env, ws_env_suffix = get_ws_env_settings()

        return {
            "matlab_path": matlab_path,
            "matlab_version": get_matlab_version(matlab_path),
            "matlab_cmd": [
                "matlab",
                "-nosplash",
                "-nodesktop",
                "-softwareopengl",
                "-r",
                f"try; run('{matlab_startup_file}'); catch; end;",
            ],
            "xvfb_cmd": [
                "Xvfb",
                ":1",
                "-screen",
                "0",
                "1600x1200x24",
                "-dpi",
                "100",
                # "-ac",
                "-extension",
                "RANDR",
                # "+render",
                # "-noreset",
            ],
            "matlab_ready_file": Path(tempfile.gettempdir()) / "connector.securePort",
            "base_url": os.environ["BASE_URL"],
            "app_port": os.environ["APP_PORT"],
            "host_interface": os.environ.get("APP_HOST"),
            "mwapikey": str(uuid.uuid4()),
            "matlab_protocol": "https",
            # TODO: Uncomment this ?
            # "matlab_display": ":1",
            "nlm_conn_str": os.environ.get("MLM_LICENSE_FILE"),
            "matlab_config_file": Path.home() / ".matlab" / "proxy_app_config.json",
            "ws_env": ws_env,
            "mwa_api_endpoint": f"https://login{ws_env_suffix}.mathworks.com/authenticationws/service/v4",
            "mhlm_api_endpoint": f"https://licensing{ws_env_suffix}.mathworks.com/mls/service/v1/entitlement/list",
            "mwa_login": f"https://login{ws_env_suffix}.mathworks.com",
        }
