# Copyright 2020-2025 The MathWorks, Inc.

import inspect
import os
from pathlib import Path

import matlab_proxy
import matlab_proxy_manager
import pytest
from matlab_proxy.constants import MWI_AUTH_TOKEN_NAME_FOR_HTTP
from matlab_proxy.util.mwi import environment_variables as mwi_env
from matlab_proxy_manager.utils import constants
from matlab_proxy_manager.utils import environment_variables as mpm_env

import jupyter_matlab_proxy
from jupyter_matlab_proxy.jupyter_config import config


@pytest.fixture
def set_mwi_use_fallback_kernel(monkeypatch):
    """monkeypatch the _USE_FALLBACK_KERNEL attribute to set it to true
    for tests that are testing jupyter-based workflow"""
    monkeypatch.setattr("jupyter_matlab_proxy._USE_FALLBACK_KERNEL", True)


def test_get_auth_token():
    """Tests if _get_auth_token() function returns a token and token_hash as a dict by default."""
    r = jupyter_matlab_proxy._get_auth_token()
    assert r is not None
    assert r.get("token") is not None
    assert r.get("token_hash") is not None


def test_get_auth_token_with_token_auth_disabled(monkeypatch):
    """Tests if _get_auth_token() function returns None if token authentication is explicitly disabled."""
    monkeypatch.setenv(mwi_env.get_env_name_enable_mwi_auth_token(), "False")
    r = jupyter_matlab_proxy._get_auth_token()
    assert r is None


def test_get_env(set_mwi_use_fallback_kernel):
    """Tests if _get_env() method returns the expected enviroment settings as a dict."""

    port = 10000
    base_url = "/foo/"
    r = jupyter_matlab_proxy._get_env(port, base_url)
    assert r.get(mwi_env.get_env_name_app_port()) == str(port)
    assert r.get(mwi_env.get_env_name_base_url()) == f"{base_url}matlab"
    assert r.get(mwi_env.get_env_name_enable_mwi_auth_token()) == "True"
    assert r.get(
        mwi_env.get_env_name_mwi_auth_token()
    ) == jupyter_matlab_proxy._mwi_auth_token.get("token")


def test_get_env_with_token_auth_disabled(set_mwi_use_fallback_kernel, monkeypatch):
    """Tests if _get_env() method returns the expected enviroment settings as a dict
    when token authentication is explicitly disabled.
    """

    port = 10000
    base_url = "/foo/"
    monkeypatch.setattr(jupyter_matlab_proxy, "_mwi_auth_token", None)
    r = jupyter_matlab_proxy._get_env(port, base_url)
    assert r.get(mwi_env.get_env_name_app_port()) == str(port)
    assert r.get(mwi_env.get_env_name_base_url()) == f"{base_url}matlab"
    assert r.get(mwi_env.get_env_name_enable_mwi_auth_token()) is None
    assert r.get(mwi_env.get_env_name_mwi_auth_token()) is None


def test_get_env_with_proxy_manager(monkeypatch):
    """Tests if _get_env() method returns the expected environment settings as a dict."""
    # Setup
    monkeypatch.setattr("jupyter_matlab_proxy._USE_FALLBACK_KERNEL", False)
    monkeypatch.setattr("jupyter_matlab_proxy._MPM_AUTH_TOKEN", "secret")
    monkeypatch.setattr("jupyter_matlab_proxy._JUPYTER_SERVER_PID", "123")
    mpm_port = 10000
    r = jupyter_matlab_proxy._get_env(mpm_port, None)
    assert r.get(mpm_env.get_env_name_mwi_mpm_port()) == str(mpm_port)
    assert r.get(mpm_env.get_env_name_mwi_mpm_auth_token()) == "secret"
    assert r.get(mpm_env.get_env_name_mwi_mpm_parent_pid()) == "123"


def test_setup_matlab(set_mwi_use_fallback_kernel):
    """Tests for a valid Server Process Configuration Dictionary

    This test checks if the jupyter proxy returns the expected Server Process Configuration
    Dictionary for the Matlab process.
    """
    # Setup
    package_path = Path(inspect.getfile(jupyter_matlab_proxy)).parent
    icon_path = str(package_path / "icon_open_matlab.svg")

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
            "title": "Open MATLAB",
            "icon_path": icon_path,
        },
        "request_headers_override": {
            MWI_AUTH_TOKEN_NAME_FOR_HTTP: jupyter_matlab_proxy._mwi_auth_token.get(
                "token_hash"
            ),
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    assert expected_matlab_setup == actual_matlab_setup
    assert os.path.isfile(actual_matlab_setup["launcher_entry"]["icon_path"])


def test_setup_matlab_with_proxy_manager(monkeypatch):
    """Tests for a valid Server Process Configuration Dictionary

    This test checks if the jupyter proxy returns the expected Server Process Configuration
    Dictionary for the Matlab process.
    """

    # Setup
    monkeypatch.setattr("jupyter_matlab_proxy._USE_FALLBACK_KERNEL", False)
    monkeypatch.setattr("jupyter_matlab_proxy._MPM_AUTH_TOKEN", "secret")
    monkeypatch.setattr("jupyter_matlab_proxy._JUPYTER_SERVER_PID", "123")
    package_path = Path(inspect.getfile(jupyter_matlab_proxy)).parent
    icon_path = str(package_path / "icon_open_matlab.svg")

    expected_matlab_setup = {
        "command": [matlab_proxy_manager.get_executable_name()],
        "timeout": 100,
        "environment": jupyter_matlab_proxy._get_env,
        "absolute_url": True,
        "launcher_entry": {
            "title": "Open MATLAB",
            "icon_path": icon_path,
        },
        "request_headers_override": {
            constants.HEADER_MWI_MPM_CONTEXT: "123",
            constants.HEADER_MWI_MPM_AUTH_TOKEN: "secret",
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    assert expected_matlab_setup == actual_matlab_setup
    assert os.path.isfile(actual_matlab_setup["launcher_entry"]["icon_path"])


def test_setup_matlab_with_token_auth_disabled(
    set_mwi_use_fallback_kernel, monkeypatch
):
    """Tests for a valid Server Process Configuration Dictionary

    This test checks if the jupyter proxy returns the expected Server Process Configuration
    Dictionary for the Matlab process when token authentication is explicitly disabled.
    """
    # Setup
    package_path = Path(inspect.getfile(jupyter_matlab_proxy)).parent
    icon_path = str(package_path / "icon_open_matlab.svg")
    monkeypatch.setattr(jupyter_matlab_proxy, "_mwi_auth_token", None)

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
            "title": "Open MATLAB",
            "icon_path": icon_path,
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    assert expected_matlab_setup == actual_matlab_setup
    assert os.path.isfile(actual_matlab_setup["launcher_entry"]["icon_path"])
