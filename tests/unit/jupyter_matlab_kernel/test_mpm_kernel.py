# Copyright 2024-2025 The MathWorks, Inc.

import uuid

import pytest

from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError


@pytest.fixture
def mpm_kernel_instance(mocker) -> MATLABKernelUsingMPM:
    # Mock logger
    mock_logger = mocker.Mock()

    # Use pytest-mock's mocker fixture to patch the function and log attribute
    mocker.patch(
        "jupyter_matlab_kernel.base_kernel.BaseMATLABKernel._extract_kernel_id_from_sys_args",
        return_value=uuid.uuid4().hex,
    )
    mocker.patch(
        "jupyter_matlab_kernel.base_kernel.BaseMATLABKernel.log",
        new=mock_logger,
    )

    return MATLABKernelUsingMPM()


@pytest.mark.asyncio
async def test_initialize_matlab_proxy_with_mpm_success(mocker, mpm_kernel_instance):
    mpm_lib_start_matlab_proxy_response = {
        "absolute_url": "dummyURL",
        "mwi_base_url": "/matlab/dummy",
        "headers": "dummy_header",
        "mpm_auth_token": "dummy_token",
    }

    # Use pytest-mock's mocker fixture to patch the function
    mocker.patch(
        "matlab_proxy_manager.lib.api.start_matlab_proxy_for_kernel",
        return_value=mpm_lib_start_matlab_proxy_response,
    )

    # Call the method and assert the result
    result = await mpm_kernel_instance._initialize_matlab_proxy_with_mpm(
        mpm_kernel_instance.log
    )
    expected_response = tuple(mpm_lib_start_matlab_proxy_response.values())
    assert result == expected_response


async def test_initialize_matlab_proxy_with_mpm_exception(mocker, mpm_kernel_instance):
    # Use pytest-mock's mocker fixture to patch the function
    mocker.patch(
        "matlab_proxy_manager.lib.api.start_matlab_proxy_for_kernel",
        side_effect=Exception("Simulated failure"),
    )

    with pytest.raises(MATLABConnectionError) as exc_info:
        await mpm_kernel_instance._initialize_matlab_proxy_with_mpm(
            mpm_kernel_instance.log
        )
    assert "Simulated failure" in str(exc_info.value)


async def test_initialize_mwi_comm_helper(mocker, mpm_kernel_instance):
    # Mock the necessary attributes
    mpm_kernel_instance.io_loop = mocker.Mock()
    mpm_kernel_instance.io_loop.asyncio_loop = mocker.Mock()

    mpm_kernel_instance.control_thread = mocker.Mock()
    mpm_kernel_instance.control_thread.io_loop = mocker.Mock()
    mpm_kernel_instance.control_thread.io_loop.asyncio_loop = mocker.Mock()

    # Mock MWICommHelper
    mock_mwi_comm_helper = mocker.patch(
        "jupyter_matlab_kernel.mpm_kernel.MWICommHelper", autospec=True
    )
    mock_mwi_comm_helper_instance = mock_mwi_comm_helper.return_value
    mock_mwi_comm_helper_instance.connect = mocker.AsyncMock()

    # Test parameters
    murl = "http://proxy-url.com"
    headers = {"MWI_AUTH_TOKEN": "test_token"}

    # Run the test method
    await mpm_kernel_instance._initialize_mwi_comm_helper(murl, headers)

    # Assertions
    mock_mwi_comm_helper.assert_called_once_with(
        mpm_kernel_instance.kernel_id,
        murl,
        mpm_kernel_instance.io_loop.asyncio_loop,
        mpm_kernel_instance.control_thread.io_loop.asyncio_loop,
        headers,
        mpm_kernel_instance.log,
    )
    mock_mwi_comm_helper_instance.connect.assert_awaited_once()

    # Verify that the mwi_comm_helper instance variable is set
    assert mpm_kernel_instance.mwi_comm_helper == mock_mwi_comm_helper_instance


def test_process_children_return_empty_list(mpm_kernel_instance):
    assert mpm_kernel_instance._process_children() == []


async def test_do_shutdown_success(mocker, mpm_kernel_instance):
    mpm_kernel_instance.is_matlab_assigned = True

    # Mock the mwi_comm_helper and its methods
    mpm_kernel_instance.mwi_comm_helper = mocker.Mock()
    mpm_kernel_instance.mwi_comm_helper.send_shutdown_request_to_matlab = (
        mocker.AsyncMock()
    )
    mpm_kernel_instance.mwi_comm_helper.disconnect = mocker.AsyncMock()

    # Mock the mpm_lib.shutdown function
    mock_shutdown = mocker.patch(
        "matlab_proxy_manager.lib.api.shutdown", return_value=mocker.AsyncMock()
    )
    # Call the method
    restart = False
    await mpm_kernel_instance.do_shutdown(restart)

    # Assertions
    mpm_kernel_instance.mwi_comm_helper.send_shutdown_request_to_matlab.assert_awaited_once()
    mpm_kernel_instance.mwi_comm_helper.disconnect.assert_awaited_once()
    mock_shutdown.assert_awaited_once_with(
        mpm_kernel_instance.parent_pid,
        mpm_kernel_instance.kernel_id,
        mpm_kernel_instance.mpm_auth_token,
    )
    assert not mpm_kernel_instance.is_matlab_assigned
    mpm_kernel_instance.log.debug.assert_any_call(
        "Received shutdown request from Jupyter"
    )


async def test_do_shutdown_exception(mocker, mpm_kernel_instance):
    mpm_kernel_instance.is_matlab_assigned = True

    # Mock the mwi_comm_helper and its methods
    mpm_kernel_instance.mwi_comm_helper = mocker.Mock()
    mpm_kernel_instance.mwi_comm_helper.send_shutdown_request_to_matlab = (
        mocker.AsyncMock(side_effect=MATLABConnectionError("Test connection error"))
    )
    mpm_kernel_instance.mwi_comm_helper.disconnect = mocker.AsyncMock()

    # Mock the mpm_lib.shutdown function
    mock_shutdown = mocker.patch(
        "matlab_proxy_manager.lib.api.shutdown", return_value=mocker.AsyncMock()
    )
    # Call the method
    restart = False
    await mpm_kernel_instance.do_shutdown(restart)

    # Assertions
    mpm_kernel_instance.mwi_comm_helper.send_shutdown_request_to_matlab.assert_awaited_once()

    # Not awaited since there was an exception right above
    mpm_kernel_instance.mwi_comm_helper.disconnect.assert_not_awaited()
    mock_shutdown.assert_awaited_once_with(
        mpm_kernel_instance.parent_pid,
        mpm_kernel_instance.kernel_id,
        mpm_kernel_instance.mpm_auth_token,
    )
    assert not mpm_kernel_instance.is_matlab_assigned
