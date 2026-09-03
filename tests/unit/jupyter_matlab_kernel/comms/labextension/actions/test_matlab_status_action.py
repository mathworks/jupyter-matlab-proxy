# Copyright 2026 The MathWorks, Inc.

import pytest
from jupyter_matlab_kernel.comms.labextension.actions import MatlabStatusAction
from jupyter_matlab_kernel.comms.labextension.actions.types import ActionTypes


@pytest.fixture
def mock_kernel(mocker):
    """Create a mock kernel for testing."""
    kernel = mocker.MagicMock()
    kernel.log = mocker.MagicMock()
    kernel.mwi_comm_helper = mocker.MagicMock()
    return kernel


@pytest.fixture
def mock_comm(mocker):
    """Create a mock comm object for testing."""
    return mocker.MagicMock()


@pytest.fixture
def matlab_status_action(mock_kernel):
    """Create a MatlabStatusAction instance for testing."""
    return MatlabStatusAction(mock_kernel)


def test_init_sets_kernel_and_log(mock_kernel):
    """Test that initialization sets kernel and log attributes."""
    # Act
    action = MatlabStatusAction(mock_kernel)

    # Assert
    assert action.kernel is mock_kernel
    assert action.log is mock_kernel.log


def test_get_code_returns_none(matlab_status_action):
    """Test that get_code returns None."""
    # Act & Assert
    assert matlab_status_action.get_code() is None


def test_validate_data_returns_none(matlab_status_action):
    """Test that validate_data returns None."""
    # Act & Assert
    assert matlab_status_action.validate_data({}) is None


@pytest.mark.asyncio
async def test_execute_fetches_and_sends_status(
    matlab_status_action, mock_comm, mocker
):
    """Test that execute fetches status and sends response."""
    # Arrange
    mock_status = mocker.MagicMock()
    mock_status.is_matlab_licensed = True
    mock_status.matlab_status = "running"
    mock_status.to_dict.return_value = {
        "isMatlabLicensed": True,
        "matlabStatus": "running",
    }
    matlab_status_action.kernel.mwi_comm_helper.fetch_matlab_proxy_status = (
        mocker.AsyncMock(return_value=mock_status)
    )

    # Act
    await matlab_status_action.execute(mock_comm, {})

    # Assert
    matlab_status_action.kernel.mwi_comm_helper.fetch_matlab_proxy_status.assert_called_once()
    mock_status.to_dict.assert_called_once_with(camel_case=True)
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.MATLAB_STATUS.value
    assert call_args["data"] == {"isMatlabLicensed": True, "matlabStatus": "running"}
    assert call_args["error"] is None
    assert matlab_status_action.log.debug.call_count >= 1


@pytest.mark.asyncio
async def test_execute_sends_error_on_exception(
    matlab_status_action, mock_comm, mocker
):
    """Test that execute sends error response when fetch fails."""
    # Arrange
    error_message = "Connection failed"
    matlab_status_action.kernel.mwi_comm_helper.fetch_matlab_proxy_status = (
        mocker.AsyncMock(side_effect=Exception(error_message))
    )

    # Act
    await matlab_status_action.execute(mock_comm, {})

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.MATLAB_STATUS.value
    assert call_args["data"] is None
    assert call_args["error"] == error_message
    matlab_status_action.log.error.assert_called_once()
