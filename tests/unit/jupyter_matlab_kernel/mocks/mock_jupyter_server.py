# Copyright 2023-2024 The MathWorks, Inc.
"""Mocks matlab-proxy integration with Jupyter Server.

This module provides a pytest fixture that mocks how matlab-proxy integrates
with Jupyter server.
"""

import http
import os

import pytest
import requests
from jupyter_server import serverapp

PID = "server 1"
PORT = "1234"
BASE_URL = "/server_of_nb/"
SECURE = False
TEST_TOKEN = "test_token"
LICENSING = True
AUTHORIZED_HEADERS = {"Authorization": "token test_token"}
PASSWORD = ""
HOSTNAME = "localhost"
URL = f"http://{HOSTNAME}:{PORT}{BASE_URL}"
SECURE_URL = f"https://{HOSTNAME}:{PORT}{BASE_URL}"


@pytest.fixture
def MockJupyterServerFixture(monkeypatch):
    """Mock the matlab-proxy integration with JupyterServer.

    This fixture provides the mocked calls to emulate that an instance of matlab proxy
    is running.
    """

    def fake_getppid():
        return PID

    def fake_list_running_servers(*args, **kwargs):
        return [
            {
                "pid": PID,
                "port": PORT,
                "base_url": BASE_URL,
                "secure": SECURE,
                "token": TEST_TOKEN,
                "password": PASSWORD,
                "hostname": HOSTNAME,
                "url": URL,
            }
        ]

    class MockResponse:
        def __init__(
            self, status_code=http.HTTPStatus.OK, text="MWI_MATLAB_PROXY_IDENTIFIER"
        ) -> None:
            self.status_code = status_code
            self.text = text

        @staticmethod
        def json():
            return {
                "licensing": LICENSING,
                "matlab": {"status": "up"},
                "error": False,
            }

    def mock_get(*args, **kwargs):
        # Return a successful matlab_proxy startup message if there is any header present,
        # else return an unsuccessful result (via status codes other than 200)
        if "headers" in kwargs and kwargs["headers"]:
            return MockResponse()
        else:
            return MockResponse(status_code=http.HTTPStatus.SERVICE_UNAVAILABLE)

    monkeypatch.setattr(serverapp, "list_running_servers", fake_list_running_servers)
    monkeypatch.setattr(os, "getppid", fake_getppid)
    monkeypatch.setattr(requests, "get", mock_get)
    yield
