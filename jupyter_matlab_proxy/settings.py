# Copyright 2020 The MathWorks, Inc.

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
    """ Get the MATLAB Release version in this image"""

    if matlab_path is None:
        return None

    tree = ET.parse(matlab_path / "VersionInfo.xml")
    root = tree.getroot()
    return root.find("release").text


def get(dev=False):
    devel_file = Path(__file__).resolve().parent / "./devel.py"
    matlab_startup_file = str(Path(__file__).resolve().parent / "matlab" / "startup.m")
    matlab_ready_file = Path(tempfile.mkstemp()[1])
    ws_env = (os.getenv("WS_ENV") or "").lower()
    ws_env_suffix = f"-{ws_env}" if "integ" in ws_env else ""

    if dev:
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
            "mwa_api_endpoint": f"https://login{ws_env_suffix}.mathworks.com/authenticationws/service/v4",
            "mhlm_api_endpoint": f"https://licensing{ws_env_suffix}.mathworks.com/mls/service/v1/entitlement/list",
            "mwa_login": f"https://login{ws_env_suffix}.mathworks.com",
        }
    else:
        matlab_path = get_matlab_path()
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
            "matlab_display": ":1",
            "nlm_conn_str": os.environ.get("MLM_LICENSE_FILE"),
            "matlab_config_file": Path.home() / ".matlab" / "proxy_app_config.json",
            "mwa_api_endpoint": f"https://login{ws_env_suffix}.mathworks.com/authenticationws/service/v4",
            "mhlm_api_endpoint": f"https://licensing{ws_env_suffix}.mathworks.com/mls/service/v1/entitlement/list",
            "mwa_login": f"https://login{ws_env_suffix}.mathworks.com",
        }
