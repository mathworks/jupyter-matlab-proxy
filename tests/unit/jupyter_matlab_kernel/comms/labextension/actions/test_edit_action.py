# Copyright 2026 The MathWorks, Inc.

import pytest
from jupyter_matlab_kernel.comms.labextension.actions import EditAction
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
def edit_action(mock_kernel):
    """Create an EditAction instance for testing."""
    return EditAction(mock_kernel)


def test_init_sets_kernel_and_log(mock_kernel):
    """Test that initialization sets kernel and log attributes."""
    # Act
    action = EditAction(mock_kernel)

    # Assert
    assert action.kernel is mock_kernel
    assert action.log is mock_kernel.log


def test_get_code_returns_edit_command(edit_action):
    """Test that get_code returns correct MATLAB edit command."""
    # Act
    result = edit_action.get_code("/path/to/file.mlx")

    # Assert
    assert result == "edit('/path/to/file.mlx');"


def test_validate_data(edit_action):
    """Test validate_data raises for invalid data and succeeds for valid data."""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        edit_action.validate_data({})
    assert "liveCodeFilePath" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        edit_action.validate_data({"other_key": "value"})
    assert "liveCodeFilePath" in str(exc_info.value)

    edit_action.validate_data({"liveCodeFilePath": "/path/to/file.mlx"})


@pytest.mark.parametrize(
    "response_str,expected",
    [
        pytest.param("  State: RUNNING", True, id="running"),
        pytest.param("  State: STOPPED", False, id="stopped"),
        pytest.param("  State: INITIALIZING", False, id="initializing"),
    ],
)
def test_check_if_rootapp_instance_is_set(edit_action, response_str, expected):
    """Test rootapp instance state checking."""
    # Act
    result = edit_action._EditAction__check_if_rootapp_instance_is_set(response_str)

    # Assert
    assert result == expected


def test_check_if_rootapp_instance_is_set_raises_error(edit_action):
    """Test that rootapp check raises exception when response cannot be parsed."""
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        edit_action._EditAction__check_if_rootapp_instance_is_set("no info")
    assert "Failed to parse response string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_sends_error_on_validation_failure(edit_action, mock_comm):
    """Test that execute sends error response when validation fails."""
    # Act
    await edit_action.execute(mock_comm, {})

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.EDIT.value
    assert call_args["error"] is not None
    edit_action.log.error.assert_called_once()


@pytest.mark.asyncio
async def test_execute_opens_file_successfully(edit_action, mock_comm, mocker):
    """Test successful file opening in MATLAB editor."""
    # Arrange
    mocker.patch.object(
        edit_action,
        "_EditAction__wait_for_rootapp_instance_to_be_set",
        new=mocker.AsyncMock(),
    )
    edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab = mocker.AsyncMock(
        return_value={"isError": False, "responseStr": ""}
    )
    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    data = {"liveCodeFilePath": "~/file.mlx"}

    # Act
    await edit_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.EDIT.value
    assert call_args["error"] is None
    edit_action.log.info.assert_called()


@pytest.mark.asyncio
async def test_execute_sends_error_on_edit_request_failure(
    edit_action, mock_comm, mocker
):
    """Test that execute sends error when edit request fails."""
    # Arrange
    mocker.patch.object(
        edit_action,
        "_EditAction__wait_for_rootapp_instance_to_be_set",
        new=mocker.AsyncMock(),
    )
    edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab = mocker.AsyncMock(
        return_value={"isError": True, "responseStr": "Edit failed"}
    )
    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    data = {"liveCodeFilePath": "~/file.mlx"}

    # Act
    await edit_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.EDIT.value
    assert call_args["error"] is not None


@pytest.mark.asyncio
async def test_execute_sends_error_on_rootapp_timeout(edit_action, mock_comm, mocker):
    """Test that execute sends error when rootapp wait times out."""
    # Arrange
    mocker.patch.object(
        edit_action,
        "_EditAction__wait_for_rootapp_instance_to_be_set",
        new=mocker.AsyncMock(side_effect=TimeoutError("Timeout")),
    )

    data = {"liveCodeFilePath": "~/file.mlx"}

    # Act
    await edit_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.EDIT.value
    assert "Timeout" in call_args["error"]


@pytest.mark.asyncio
async def test_wait_for_rootapp_instance_succeeds_immediately(edit_action, mocker):
    """Test wait for rootapp succeeds when instance is already running."""
    # Arrange
    edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab = mocker.AsyncMock(
        return_value={"isError": False, "responseStr": "  State: RUNNING"}
    )

    # Act
    await edit_action._EditAction__wait_for_rootapp_instance_to_be_set()

    # Assert
    edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab.assert_called()


@pytest.mark.asyncio
async def test_wait_for_rootapp_instance_retries_until_running(edit_action, mocker):
    """Test wait for rootapp retries until instance is running."""
    # Arrange
    edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab = mocker.AsyncMock(
        side_effect=[
            {"isError": False, "responseStr": "  State: INITIALIZING"},
            {"isError": False, "responseStr": "  State: INITIALIZING"},
            {"isError": False, "responseStr": "  State: RUNNING"},
        ]
    )
    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    # Act
    await edit_action._EditAction__wait_for_rootapp_instance_to_be_set()

    # Assert
    assert (
        edit_action.kernel.mwi_comm_helper.send_eval_request_to_matlab.call_count == 3
    )
