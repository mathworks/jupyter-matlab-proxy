# Copyright 2023 The MathWorks, Inc.

# This file contains tests for jupyter_matlab_kernel.mwi_comm_helpers
from jupyter_matlab_kernel.mwi_comm_helpers import (
    fetch_matlab_proxy_status,
    send_interrupt_request_to_matlab,
    send_execution_request_to_matlab,
)

import pytest
import requests
from requests.exceptions import HTTPError

from mocks.mock_http_responses import (
    MockUnauthorisedRequestResponse,
    MockMatlabProxyStatusResponse,
    MockSimpleBadResponse,
)


# Testing fetch_matlab_proxy_status
def test_fetch_matlab_proxy_status_unauth_request(monkeypatch):
    """
    This test checks that fetch_matlab_proxy_status throws an exception
    if the matlab-proxy HTTP request is unauthorised.
    """

    def mock_get(*args, **kwargs):
        return MockUnauthorisedRequestResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(HTTPError) as exceptionInfo:
        fetch_matlab_proxy_status("", "{}")
    assert MockUnauthorisedRequestResponse().exception_msg in str(exceptionInfo.value)


def test_fetch_matlab_proxy_status(monkeypatch):
    """
    This test checks that fetch_matlab_proxy_status returns the correct
    values for a valid request to matlab-proxy.
    """

    def mock_get(*args, **kwargs):
        return MockMatlabProxyStatusResponse(True, "up", False)

    monkeypatch.setattr(requests, "get", mock_get)

    (
        is_matlab_licened,
        matlab_status,
        matlab_proxy_has_error,
    ) = fetch_matlab_proxy_status("", "{}")
    assert is_matlab_licened == True
    assert matlab_status == "up"
    assert matlab_proxy_has_error == True


def test_interrupt_request_bad_request(monkeypatch):
    """
    This test checks that send_interrupt_request_to_matlab raises
    an exception if the response to the HTTP post is not valid.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    monkeypatch.setattr(requests, "post", mock_post)

    with pytest.raises(HTTPError) as exceptionInfo:
        send_interrupt_request_to_matlab("", {})
    assert mock_exception_message in str(exceptionInfo.value)


# Testing send_execution_request_to_matlab
def test_execution_request_bad_request(monkeypatch):
    """
    This test checks that send_execution_request_to_matlab throws an exception
    if the response to the HTTP request is invalid.
    """
    mock_exception_message = "Mock exception thrown due to bad request status."

    def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    monkeypatch.setattr(requests, "post", mock_post)

    url = ""
    headers = {}
    code = "placeholder for code"
    with pytest.raises(HTTPError) as exceptionInfo:
        send_execution_request_to_matlab(url, headers, code)
    assert mock_exception_message in str(exceptionInfo.value)


def test_execution_request_invalid_feval_response(monkeypatch):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the response from the feval command is invalid.
    """
    mock_exception_message = "Mock exception thrown due to invalid feval response."

    class MockSimpleInvalidFevalResponse:
        status_code = requests.codes.ok

        def raise_for_status(self):
            raise HTTPError(mock_exception_message)

        @staticmethod
        def json():
            return {"messages": {}}

    def mock_post(*args, **kwargs):
        return MockSimpleInvalidFevalResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    url = ""
    headers = {}
    code = "placeholder for code"
    with pytest.raises(HTTPError) as exceptionInfo:
        send_execution_request_to_matlab(url, headers, code)
    assert str(exceptionInfo.value) == ""


def test_execution_interrupt(monkeypatch):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the matlab command appears to have been interupted.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    class MockResponse:
        status_code = requests.codes.ok

        def raise_for_status(self):
            raise HTTPError(mock_exception_message)

        @staticmethod
        def json():
            return {
                "messages": {
                    "FEvalResponse": [
                        {},
                        {
                            "isError": True,
                            "results": ["Mock results from feval"],
                            "messageFaults": [{"message": ""}],
                        },
                    ],
                }
            }

    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    url = ""
    headers = {}
    code = "placeholder for code"
    with pytest.raises(Exception) as exceptionInfo:
        send_execution_request_to_matlab(url, headers, code)
    assert "Operation may have interrupted by user" in str(exceptionInfo.value)


def test_execution_success(monkeypatch):
    """
    This test checks that send_execution_request_to_matlab returns the correct information
    from a valid response from MATLAB.
    """

    class MockResponse:
        status_code = requests.codes.ok

        @staticmethod
        def json():
            return {
                "messages": {
                    "FEvalResponse": [
                        {},
                        {
                            "isError": False,
                            "results": ["Mock results from feval"],
                            "messageFaults": [{"message": ""}],
                        },
                    ],
                }
            }

    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    url = ""
    headers = {}
    code = "placeholder for code"
    try:
        outputs = send_execution_request_to_matlab(url, headers, code)
    except Exception as exceptionInfo:
        pytest.fail("Unexpected failured in execution request")

    assert "Mock results from feval" in outputs
