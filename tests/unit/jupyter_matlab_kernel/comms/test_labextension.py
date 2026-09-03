# Copyright 2025-2026 The MathWorks, Inc.

import pytest
from jupyter_matlab_kernel.comms.labextension import (
    LabExtensionCommunication,
)

from unittest.mock import call


@pytest.fixture
def mock_kernel(mocker):
    """Create a mock kernel for testing."""
    kernel = mocker.MagicMock()
    return kernel


@pytest.fixture
def mock_stream(mocker):
    """Create a mock stream for testing."""
    stream = mocker.MagicMock()
    return stream


@pytest.fixture
def mock_ident(mocker):
    """Create a mock ident for testing."""
    ident = mocker.MagicMock()
    return ident


@pytest.fixture
def mock_comm(mocker):
    """Create a mock comm object for testing."""
    comm = mocker.MagicMock()
    return comm


@pytest.fixture
def labext_comm(mock_kernel):
    """Create a LabExtensionCommunication instance for testing."""
    return LabExtensionCommunication(mock_kernel)


def test_init(mock_kernel):
    """Test that LabExtensionCommunication initializes correctly."""
    labext_comm = LabExtensionCommunication(mock_kernel)

    assert labext_comm.comms == {}
    assert labext_comm.kernel is mock_kernel
    assert labext_comm.log is mock_kernel.log


def test_comm_open_creates_comm(
    labext_comm, mocker, mock_stream, mock_ident, mock_comm
):
    """Test that comm_open creates a communication channel."""
    # Arrange
    # Mock the Comm class
    mock_comm_class = mocker.patch(
        "jupyter_matlab_kernel.comms.labextension.labextension.Comm",
        return_value=mock_comm,
    )

    test_comm_id = "test-comm-id"
    test_target_name = "test-target"
    msg = {"content": {"comm_id": test_comm_id, "target_name": test_target_name}}

    # Act
    labext_comm.comm_open(mock_stream, mock_ident, msg)

    # Assert
    mock_comm_class.assert_called_once_with(
        comm_id=test_comm_id, primary=False, target_name=test_target_name
    )

    # Verify comm is set
    assert labext_comm.comms[test_comm_id] is mock_comm
    # Verify debug is called twice and with the right messages
    assert labext_comm.log.debug.call_count == 2
    expected_calls = [
        call(
            f"Received comm_open message with id: {test_comm_id} and target_name: {test_target_name}"
        ),
        call(
            f"Successfully created communication channel with labextension on: {test_comm_id}"
        ),
    ]
    labext_comm.log.debug.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.asyncio
async def test_comm_msg_with_valid_comm(
    labext_comm, mock_stream, mock_ident, mock_comm, mocker
):
    """Test that comm_msg processes messages and executes action."""
    # Arrange
    comm_id = "test-comm-id"
    labext_comm.comms[comm_id] = mock_comm

    test_action = "test-action"
    test_data = {"key": "value"}
    msg = {
        "content": {
            "comm_id": comm_id,
            "data": {"action": test_action, "data": test_data},
        }
    }

    mock_action = mocker.MagicMock()
    mock_action.execute = mocker.AsyncMock()
    mock_action.__class__.__name__ = "TestAction"
    mock_create_action = mocker.patch(
        "jupyter_matlab_kernel.comms.labextension.labextension.ActionFactory.create_action",
        return_value=mock_action,
    )

    # Act
    await labext_comm.comm_msg(mock_stream, mock_ident, msg)

    # Assert
    mock_create_action.assert_called_once_with(test_action, labext_comm.kernel)
    mock_action.execute.assert_called_once_with(mock_comm, test_data)
    assert labext_comm.log.debug.call_count == 2


@pytest.mark.asyncio
async def test_comm_msg_ignores_unknown_comm_id(labext_comm, mock_stream, mock_ident):
    """Test that comm_msg logs an error and returns when comm_id is not found."""
    # Arrange
    comm_id = "unknown-comm-id"
    msg = {
        "content": {
            "comm_id": comm_id,
            "data": {"action": "test-action", "data": {}},
        }
    }

    # Act
    await labext_comm.comm_msg(mock_stream, mock_ident, msg)

    # Assert
    labext_comm.log.error.assert_called_once()


@pytest.mark.asyncio
async def test_comm_msg_logs_error_on_action_execute_failure(
    labext_comm, mock_stream, mock_ident, mock_comm, mocker
):
    """Test that comm_msg logs error when action.execute fails."""
    # Arrange
    comm_id = "test-comm-id"
    labext_comm.comms[comm_id] = mock_comm

    msg = {
        "content": {
            "comm_id": comm_id,
            "data": {"action": "test-action", "data": {}},
        }
    }

    error_message = "Action execution failed"
    mock_action = mocker.MagicMock()
    mock_action.execute = mocker.AsyncMock(side_effect=Exception(error_message))
    mock_action.__class__.__name__ = "TestAction"
    mocker.patch(
        "jupyter_matlab_kernel.comms.labextension.labextension.ActionFactory.create_action",
        return_value=mock_action,
    )

    # Act
    await labext_comm.comm_msg(mock_stream, mock_ident, msg)

    # Assert
    labext_comm.log.error.assert_called_once()
    assert error_message in str(labext_comm.log.error.call_args)


def test_comm_close_with_valid_comm_id(labext_comm, mock_stream, mock_ident, mock_comm):
    """Test that comm_close closes the correct communication channel."""
    # Arrange
    # Set up a mock comm with matching ID
    comm_id = "test-comm-id"
    mock_comm.comm_id = comm_id
    labext_comm.comms = {comm_id: mock_comm}

    msg = {"content": {"comm_id": comm_id}}

    # Act
    labext_comm.comm_close(mock_stream, mock_ident, msg)

    # Assert
    # Verify comm is set to None
    assert labext_comm.comms == {}

    # Verify logging
    labext_comm.log.info.assert_called_once_with(f"Comm closed with id: {comm_id}")


def test_comm_close_with_non_matching_comm_id(
    labext_comm, mock_stream, mock_ident, mock_comm
):
    """Test that comm_close warns when trying to close unknown comm."""
    # Arrange
    # Set up a mock comm with different ID
    mock_comm.comm_id = "different-comm-id"
    comm_id = "test-comm-id"
    different_comm_id = "different-comm-id"
    labext_comm.comms = {different_comm_id: mock_comm}

    msg = {"content": {"comm_id": comm_id}}

    # Act
    labext_comm.comm_close(mock_stream, mock_ident, msg)

    # Assert
    # Verify comm is not changed
    assert labext_comm.comms[different_comm_id] is mock_comm

    # Verify warning logging
    labext_comm.log.debug.assert_called_once_with(
        f"Attempted to close unknown comm_id: {comm_id}"
    )


def test_comm_close_with_no_comm(labext_comm, mock_stream, mock_ident):
    """Test that comm_close warns when no comm exists."""
    # Arrange
    # Ensure comms is empty
    labext_comm.comms = {}
    test_comm_id = "test-comm-id"
    msg = {"content": {"comm_id": test_comm_id}}

    # Act
    labext_comm.comm_close(mock_stream, mock_ident, msg)

    # Assert
    # Verify comm remains None
    assert labext_comm.comms == {}

    # Verify warning logging
    labext_comm.log.debug.assert_called_once_with(
        f"Attempted to close unknown comm_id: {test_comm_id}"
    )


@pytest.mark.asyncio
async def test_comm_msg_extracts_data_correctly(
    labext_comm, mock_stream, mock_ident, mock_comm, mocker
):
    """Test that comm_msg correctly extracts action and data from message."""
    # Arrange
    comm_id = "test-comm-id"
    labext_comm.comms = {comm_id: mock_comm}
    action_type = "execute_code"
    data = {"code": "x = 1 + 1", "cell_id": "abc123"}

    msg = {
        "content": {"comm_id": comm_id, "data": {"action": action_type, "data": data}}
    }

    mock_action = mocker.MagicMock()
    mock_action.execute = mocker.AsyncMock()
    mock_action.__class__.__name__ = "TestAction"
    mocker.patch(
        "jupyter_matlab_kernel.comms.labextension.labextension.ActionFactory.create_action",
        return_value=mock_action,
    )

    # Act
    await labext_comm.comm_msg(mock_stream, mock_ident, msg)

    # Assert
    expected_log = (
        f"Received action_type:{action_type} with data:{data} from the lab extension"
    )
    labext_comm.log.debug.assert_any_call(expected_log)
