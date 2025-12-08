# Copyright 2023-2025 The MathWorks, Inc.

# This file contains tests for jupyter_matlab_kernel.kernel
import mocks.mock_jupyter_server as MockJupyterServer
import pytest
from jupyter_server import serverapp
from mocks.mock_jupyter_server import MockJupyterServerFixture

from jupyter_matlab_kernel.jsp_kernel import (
    MATLABKernelUsingJSP,
    start_matlab_proxy,
)
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError


def test_start_matlab_proxy_without_jupyter_server():
    """
    This test checks that trying to start matlab-proxy outside of a Jupyter environment
    raises an execption.
    """
    with pytest.raises(MATLABConnectionError) as exceptionInfo:
        start_matlab_proxy()

    assert (
        "MATLAB Kernel for Jupyter was unable to find the notebook server from which it was spawned"
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


async def test_matlab_not_licensed_non_jupyter(mocker):
    """
    Test case for MATLAB not being licensed in a non-Jupyter environment.

    This test mocks a MATLABKernelUsingJSP instance to simulate a non-Jupyter
    environment where MATLAB is not licensed. It checks if the appropriate
    exception (MATLABConnectionError) is raised when performing startup checks.
    """
    # Mock the kernel's jupyter_base_url attribute to simulate a non-Jupyter environment
    kernel = mocker.MagicMock(spec=MATLABKernelUsingJSP)
    kernel.jupyter_base_url = None
    kernel.startup_error = None
    kernel.mwi_comm_helper = mocker.Mock()
    kernel.mwi_comm_helper.fetch_matlab_proxy_status = mocker.AsyncMock(
        return_value=(False, "down", False)
    )

    # Mock the perform_startup_checks method to actually call the implementation
    async def mock_perform_startup_checks(*args, **kwargs):
        return await MATLABKernelUsingJSP.perform_startup_checks(
            kernel, *args, **kwargs
        )

    kernel.perform_startup_checks.side_effect = mock_perform_startup_checks

    with pytest.raises(MATLABConnectionError):
        await kernel.perform_startup_checks()
