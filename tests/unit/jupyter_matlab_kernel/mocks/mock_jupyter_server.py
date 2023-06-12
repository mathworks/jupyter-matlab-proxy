# Copyright 2023 The MathWorks, Inc.
"""Mocks matlab-proxy integration with Jupyter Server.

This module provides a pytest fixture that mocks how matlab-proxy integrates
with Jupyter server.
"""


import pytest

import requests
import os
from jupyter_server import serverapp

PID = "server 1"
PORT = "1234/"
BASE_URL = "server_of_nb/"
SECURE = False
TEST_TOKEN = "test_token"
LICENSING = True
AUTHORISED_HEADERS = {"Authorization": "token test_token"}
PASSWORD = ""


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
            }
        ]

    class MockResponse:
        status_code = requests.codes.ok
        text = "MWI_MATLAB_PROXY_IDENTIFIER"

        @staticmethod
        def json():
            return {
                "licensing": LICENSING,
                "matlab": {"status": "up"},
                "error": False,
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(serverapp, "list_running_servers", fake_list_running_servers)
    monkeypatch.setattr(os, "getppid", fake_getppid)
    monkeypatch.setattr(requests, "get", mock_get)
    yield
