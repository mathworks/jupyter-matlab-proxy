# Copyright 2023-2025 The MathWorks, Inc.
# This file contains tests for jupyter_matlab_kernel.mwi_comm_helpers

import asyncio
import http
import json
import tempfile
import os

import aiohttp
import aiohttp.client_exceptions
import pytest
from mocks.mock_http_responses import (
    MockMatlabProxyStatusResponse,
    MockSimpleBadResponse,
    MockUnauthorisedRequestResponse,
    MockEvalResponse,
    MockEvalResponseMissingData,
)

from jupyter_matlab_kernel.mwi_comm_helpers import MWICommHelper
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError


@pytest.fixture
async def matlab_proxy_fixture():
    url = "http://localhost"
    headers = {}
    kernel_id = ""
    loop = asyncio.get_event_loop()
    matlab_proxy = MWICommHelper(kernel_id, url, loop, loop, headers)
    await matlab_proxy.connect()
    yield matlab_proxy
    await matlab_proxy.disconnect()


# Testing fetch_matlab_proxy_status
async def test_fetch_matlab_proxy_status_unauth_request(
    monkeypatch, matlab_proxy_fixture
):
    """
    This test checks that fetch_matlab_proxy_status throws an exception
    if the matlab-proxy HTTP request is unauthorised.
    """

    async def mock_get(*args, **kwargs):
        return MockUnauthorisedRequestResponse()

    monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)
    with pytest.raises(aiohttp.client_exceptions.ClientError) as exceptionInfo:
        await matlab_proxy_fixture.fetch_matlab_proxy_status()
    assert MockUnauthorisedRequestResponse().exception_msg in str(exceptionInfo.value)


@pytest.mark.parametrize(
    "input_lic_type, expected_license_status",
    [
        ("mhlm_entitled", True),
        ("mhlm_unentitled", False),
        ("nlm", True),
        ("existing_license", True),
        ("default", False),
    ],
)
async def test_fetch_matlab_proxy_status(
    input_lic_type, expected_license_status, monkeypatch, matlab_proxy_fixture
):
    """
    This test checks that fetch_matlab_proxy_status returns the correct
    values for a valid request to matlab-proxy.
    """

    async def mock_get(*args, **kwargs):
        return MockMatlabProxyStatusResponse(
            lic_type=input_lic_type, matlab_status="up", has_error=False
        )

    monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)

    (
        is_matlab_licensed,
        matlab_status,
        matlab_proxy_has_error,
    ) = await matlab_proxy_fixture.fetch_matlab_proxy_status()
    assert is_matlab_licensed == expected_license_status
    assert matlab_status == "up"
    assert matlab_proxy_has_error is False


async def test_interrupt_request_bad_request(monkeypatch, matlab_proxy_fixture):
    """
    This test checks that send_interrupt_request_to_matlab raises
    an exception if the response to the HTTP post is not valid.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    async def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    with pytest.raises(aiohttp.client_exceptions.ClientError) as exceptionInfo:
        await matlab_proxy_fixture.send_interrupt_request_to_matlab()
    assert mock_exception_message in str(exceptionInfo.value)


# Testing send_execution_request_to_matlab
async def test_execution_request_bad_request(monkeypatch, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab throws an exception
    if the response to the HTTP request is invalid.
    """
    mock_exception_message = "Mock exception thrown due to bad request status."

    async def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    code = "placeholder for code"
    with pytest.raises(aiohttp.client_exceptions.ClientError) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code)
    assert mock_exception_message in str(exceptionInfo.value)


async def test_execution_request_invalid_feval_response(
    monkeypatch, matlab_proxy_fixture
):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the response from the feval command is invalid.
    """
    mock_exception_message = "Mock exception thrown due to invalid feval response."

    class MockSimpleInvalidFevalResponse:
        status = http.HTTPStatus.OK

        def raise_for_status(self):
            raise aiohttp.client_exceptions.ClientError(mock_exception_message)

        @staticmethod
        async def json():
            return {"messages": {}}

    async def mock_post(*args, **kwargs):
        return MockSimpleInvalidFevalResponse()

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    code = "placeholder for code"
    with pytest.raises(MATLABConnectionError) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code)
    assert str(exceptionInfo.value) == str(MATLABConnectionError())


async def test_execution_interrupt(monkeypatch, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the matlab command appears to have been interupted.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    class MockResponse:
        status = http.HTTPStatus.OK

        def raise_for_status(self):
            raise aiohttp.client_exceptions.ClientError(mock_exception_message)

        @staticmethod
        async def json():
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

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    code = "placeholder for code"
    with pytest.raises(Exception) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code)
    assert "Operation may have interrupted by user" in str(exceptionInfo.value)


async def test_execution_success(monkeypatch, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab returns the correct information
    from a valid response from MATLAB.
    """

    class MockResponse:
        status = http.HTTPStatus.OK

        @staticmethod
        async def json():
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

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    code = "placeholder for code"
    try:
        outputs = await matlab_proxy_fixture.send_execution_request_to_matlab(code)
    except Exception:
        pytest.fail("Unexpected failured in execution request")

    assert "Mock results from feval" in outputs


# Testing send_eval_request_to_matlab
async def test_send_eval_request_to_matlab_success(monkeypatch, matlab_proxy_fixture):
    """Test that send_eval_request_to_matlab returns eval response correctly."""

    # Arrange
    async def mock_post(*args, **kwargs):
        return MockEvalResponse(is_error=False, response_str="", message_faults=[])

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    mcode = "x = 1 + 1"

    # Act
    result = await matlab_proxy_fixture.send_eval_request_to_matlab(mcode)

    # Assert
    # Verify the eval response is returned as-is
    expected_response = {"isError": False, "responseStr": "", "messageFaults": []}
    assert result == expected_response


async def test_send_eval_request_to_matlab_with_error(
    monkeypatch, matlab_proxy_fixture
):
    """Test that send_eval_request_to_matlab returns error response correctly."""

    # Arrange
    async def mock_post(*args, **kwargs):
        return MockEvalResponse(
            is_error=True,
            response_str="Error occurred",
            message_faults=[{"message": "Syntax error"}],
        )

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    mcode = "invalid_syntax"

    # Act
    result = await matlab_proxy_fixture.send_eval_request_to_matlab(mcode)

    # Assert
    # Verify the error response is returned as-is
    expected_response = {
        "isError": True,
        "responseStr": "Error occurred",
        "messageFaults": [{"message": "Syntax error"}],
    }
    assert result == expected_response


async def test_send_eval_request_to_matlab_bad_request(
    monkeypatch, matlab_proxy_fixture
):
    """Test that send_eval_request_to_matlab raises exception for bad HTTP request."""
    # Arrange
    mock_exception_message = "Mock exception thrown due to bad request status."

    async def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    mcode = "x = 1 + 1"

    # Act
    with pytest.raises(aiohttp.client_exceptions.ClientError) as exceptionInfo:
        await matlab_proxy_fixture.send_eval_request_to_matlab(mcode)

    # Assert
    assert mock_exception_message in str(exceptionInfo.value)


async def test_send_eval_request_to_matlab_missing_eval_response(
    monkeypatch, matlab_proxy_fixture
):
    """Test that send_eval_request_to_matlab raises MATLABConnectionError for missing EvalResponse."""

    # Arrange
    async def mock_post(*args, **kwargs):
        return MockEvalResponseMissingData()

    monkeypatch.setattr(aiohttp.ClientSession, "post", mock_post)

    mcode = "x = 1 + 1"
    with pytest.raises(MATLABConnectionError):
        await matlab_proxy_fixture.send_eval_request_to_matlab(mcode)


# Testing _read_eval_response_from_file
async def test_read_eval_response_from_file_success_with_file(matlab_proxy_fixture):
    """Test _read_eval_response_from_file with successful response and file."""
    # Arrange
    # Create a temporary file with test data
    test_data = [
        {"type": "stream", "content": {"name": "stdout", "text": "Hello World"}}
    ]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(test_data, f)
        temp_file_path = f.name

    try:
        eval_response = {
            "isError": False,
            "responseStr": temp_file_path,
            "messageFaults": [],
        }

        # Act
        result = await matlab_proxy_fixture._read_eval_response_from_file(eval_response)

        # Assert
        # Verify the result
        assert result == test_data

        # Verify the file was deleted
        assert not os.path.exists(temp_file_path)

    finally:
        # Clean up in case the test failed
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def test_read_eval_response_from_file_success_without_file(matlab_proxy_fixture):
    """Test _read_eval_response_from_file with successful response but no file."""
    # Arrange
    eval_response = {
        "isError": False,
        "responseStr": "",  # Empty file path
        "messageFaults": [],
    }

    # Act
    result = await matlab_proxy_fixture._read_eval_response_from_file(eval_response)

    # Assert
    # Verify empty result returns empty list
    assert result == []


async def test_read_eval_response_from_file_error_with_message_faults(
    matlab_proxy_fixture,
):
    """Test _read_eval_response_from_file with error response containing message faults."""
    # Arrange
    eval_response = {
        "isError": True,
        "responseStr": "Error occurred",
        "messageFaults": [{"message": "Syntax error in code"}],
    }

    # Act
    with pytest.raises(
        Exception,
        match="Failed to execute. Operation may have been interrupted by user.",
    ):
        await matlab_proxy_fixture._read_eval_response_from_file(eval_response)


async def test_read_eval_response_from_file_error_without_message_faults(
    matlab_proxy_fixture,
):
    """Test _read_eval_response_from_file with error response without message faults."""

    eval_response = {
        "isError": True,
        "responseStr": "Custom error message",
        "messageFaults": [],
    }

    with pytest.raises(Exception, match="Custom error message"):
        await matlab_proxy_fixture._read_eval_response_from_file(eval_response)


async def test_read_eval_response_from_file_handles_file_deletion_error(
    matlab_proxy_fixture, monkeypatch
):
    """Test _read_eval_response_from_file handles file deletion errors gracefully."""

    # Create a temporary file with test data
    test_data = [
        {"type": "stream", "content": {"name": "stdout", "text": "Hello World"}}
    ]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(test_data, f)
        temp_file_path = f.name

    # Mock os.remove to raise an exception
    original_remove = os.remove

    def mock_remove(path):
        if path == temp_file_path:
            raise OSError("Permission denied")
        return original_remove(path)

    monkeypatch.setattr(os, "remove", mock_remove)

    try:
        eval_response = {
            "isError": False,
            "responseStr": temp_file_path,
            "messageFaults": [],
        }

        # Should not raise exception even if file deletion fails
        result = await matlab_proxy_fixture._read_eval_response_from_file(eval_response)

        # Verify the result is still correct
        assert result == test_data

    finally:
        # Clean up manually since mocked remove failed
        if os.path.exists(temp_file_path):
            original_remove(temp_file_path)


async def test_read_eval_response_from_file_with_empty_file_content(
    matlab_proxy_fixture,
):
    """Test _read_eval_response_from_file with empty file content."""

    # Create a temporary file with empty content
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write("")  # Empty content
        temp_file_path = f.name

    try:
        eval_response = {
            "isError": False,
            "responseStr": temp_file_path,
            "messageFaults": [],
        }

        result = await matlab_proxy_fixture._read_eval_response_from_file(eval_response)

        # Verify empty content returns empty list
        assert result == []

        # Verify the file was deleted
        assert not os.path.exists(temp_file_path)

    finally:
        # Clean up in case the test failed
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def test_read_eval_response_from_file_with_whitespace_only_content(
    matlab_proxy_fixture,
):
    """Test _read_eval_response_from_file with whitespace-only file content."""

    # Create a temporary file with whitespace content
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write("   \n\t  ")  # Only whitespace
        temp_file_path = f.name

    try:
        eval_response = {
            "isError": False,
            "responseStr": temp_file_path,
            "messageFaults": [],
        }

        result = await matlab_proxy_fixture._read_eval_response_from_file(eval_response)

        # Verify whitespace-only content returns empty list
        assert result == []

        # Verify the file was deleted
        assert not os.path.exists(temp_file_path)

    finally:
        # Clean up in case the test failed
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
