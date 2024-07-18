# Copyright 2023-2024 The MathWorks, Inc.

# This file contains tests for jupyter_matlab_kernel.kernel
import mocks.mock_jupyter_server as MockJupyterServer
import pytest
from jupyter_matlab_kernel.kernel import MATLABConnectionError, start_matlab_proxy
from jupyter_server import serverapp
from mocks.mock_jupyter_server import MockJupyterServerFixture


def test_start_matlab_proxy_without_jupyter_server():
    """
    This test checks that trying to start matlab-proxy outside of a Jupyter environment
    raises an execption.
    """
    with pytest.raises(MATLABConnectionError) as exceptionInfo:
        start_matlab_proxy()

    assert (
        "MATLAB Kernel for Jupyter was unable to find the notebook server from which it was spawned!"
        in str(exceptionInfo.value)
    )


def test_start_matlab_proxy(MockJupyterServerFixture):
    """
    This test checks start_matlab_proxy returns a correctly configured URL
    """

    url, server, headers = start_matlab_proxy()
    assert server == MockJupyterServer.BASE_URL
    assert headers == MockJupyterServer.AUTHORIZED_HEADERS
    expected_url = (
        "http://localhost:"
        + MockJupyterServer.PORT
        + MockJupyterServer.BASE_URL
        + "matlab"
    )
    assert url == expected_url


def test_start_matlab_proxy_secure(monkeypatch, MockJupyterServerFixture):
    """
    This test checks that start_matlab_proxy returns a HTTPS url if configured
    to do so.
    """

    def fake_list_running_servers(*args, **kwargs):
        return [
            {
                "pid": MockJupyterServer.PID,
                "port": MockJupyterServer.PORT,
                "base_url": MockJupyterServer.BASE_URL,
                "secure": True,
                "token": MockJupyterServer.TEST_TOKEN,
                "password": MockJupyterServer.PASSWORD,
                "hostname": MockJupyterServer.HOSTNAME,
                "url": MockJupyterServer.SECURE_URL,
            }
        ]

    monkeypatch.setattr(serverapp, "list_running_servers", fake_list_running_servers)

    url, _, _ = start_matlab_proxy()
    expected_url = (
        "https://localhost:"
        + MockJupyterServer.PORT
        + MockJupyterServer.BASE_URL
        + "matlab"
    )
    assert url == expected_url


def test_start_matlab_proxy_jh_api_token(monkeypatch, MockJupyterServerFixture):
    """
    The test checks that start_matlab_proxy makes use of the environment variable
    JUPYTERHUB_API_TOKEN if it is set.
    """
    token = "test_jh_token"
    monkeypatch.setattr(MockJupyterServer, "TEST_TOKEN", None)

    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", token)
    _, _, headers = start_matlab_proxy()
    assert headers == {"Authorization": f"token {token}"}
