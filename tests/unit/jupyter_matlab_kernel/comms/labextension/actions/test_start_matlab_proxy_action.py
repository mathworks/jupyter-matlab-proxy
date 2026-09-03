# Copyright 2026 The MathWorks, Inc.

import pytest
from jupyter_matlab_kernel.comms.labextension.actions import StartMatlabProxyAction
from jupyter_matlab_kernel.comms.labextension.actions.types import ActionTypes


@pytest.fixture
def mock_kernel(mocker):
    """Create a mock kernel for testing."""
    kernel = mocker.MagicMock()
    kernel.log = mocker.MagicMock()
    kernel.is_matlab_assigned = False
    kernel.start_matlab_proxy_and_comm_helper = mocker.AsyncMock()
    return kernel


@pytest.fixture
def mock_comm(mocker):
    """Create a mock comm object for testing."""
    return mocker.MagicMock()


@pytest.fixture
def start_matlab_proxy_action(mock_kernel):
    """Create a StartMatlabProxyAction instance for testing."""
    return StartMatlabProxyAction(mock_kernel)


def test_init_sets_kernel_and_log(mock_kernel):
    """Test that initialization sets kernel and log attributes."""
    # Act
    action = StartMatlabProxyAction(mock_kernel)

    # Assert
    assert action.kernel is mock_kernel
    assert action.log is mock_kernel.log


def test_get_code_returns_none(start_matlab_proxy_action):
    """Test that get_code returns None."""
    # Act & Assert
    assert start_matlab_proxy_action.get_code() is None


def test_validate_data_returns_none(start_matlab_proxy_action):
    """Test that validate_data returns None."""
    # Act & Assert
    assert start_matlab_proxy_action.validate_data({}) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "is_matlab_assigned,should_start",
    [
        pytest.param(False, True, id="starts_when_not_assigned"),
        pytest.param(True, False, id="skips_when_already_assigned"),
    ],
)
async def test_execute_starts_proxy_based_on_matlab_status(
    mock_kernel, mock_comm, is_matlab_assigned, should_start
):
    """Test that execute starts proxy only when matlab is not assigned."""
    # Arrange
    mock_kernel.is_matlab_assigned = is_matlab_assigned
    action = StartMatlabProxyAction(mock_kernel)

    # Act
    await action.execute(mock_comm, {})

    # Assert
    if should_start:
        mock_kernel.start_matlab_proxy_and_comm_helper.assert_called_once()
        assert mock_kernel.is_matlab_assigned is True
    else:
        mock_kernel.start_matlab_proxy_and_comm_helper.assert_not_called()

    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.START_MATLAB_PROXY.value
    assert call_args["error"] is None
    action.log.info.assert_called_once()


@pytest.mark.asyncio
async def test_execute_sends_error_on_exception(
    start_matlab_proxy_action, mock_comm, mocker
):
    """Test that execute sends error response when start fails."""
    # Arrange
    error_message = "Failed to start proxy"
    start_matlab_proxy_action.kernel.start_matlab_proxy_and_comm_helper = (
        mocker.AsyncMock(side_effect=Exception(error_message))
    )

    # Act
    await start_matlab_proxy_action.execute(mock_comm, {})

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.START_MATLAB_PROXY.value
    assert call_args["error"] == error_message
    start_matlab_proxy_action.log.error.assert_called_once()
