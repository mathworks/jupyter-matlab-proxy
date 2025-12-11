# Copyright 2025 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.magics.help import help
from jupyter_matlab_kernel.magics.matlab import (
    CMD_INFO,
    CMD_NEW_SESSION,
    DEDICATED_SESSION_CONFIRMATION_MSG,
    EXISTING_NEW_SESSION_ERROR,
    get_kernel_info,
    handle_new_matlab_session,
    matlab,
)
from jupyter_matlab_kernel.mwi_exceptions import MagicError


def test_help_magic():
    magic_object = help([matlab.__name__])
    before_cell_executor = magic_object.before_cell_execute()
    output = next(before_cell_executor)
    expected_output = matlab.info_about_magic
    assert expected_output in output["value"][0]


@pytest.mark.parametrize(
    "parameters",
    [
        pytest.param([], id="atleast one argument is required"),
        pytest.param(
            ["invalid"],
            id="Invalid argument should throw exception",
        ),
        pytest.param(
            [CMD_INFO, CMD_NEW_SESSION],
            id="more than one parameter should throw exception",
        ),
    ],
)
def test_matlab_magic_exceptions(parameters):
    magic_object = matlab(parameters)
    before_cell_executor = magic_object.before_cell_execute()
    with pytest.raises(MagicError):
        next(before_cell_executor)


@pytest.mark.parametrize(
    "parameters, parameter_pos, cursor_pos, expected_output",
    [
        pytest.param(
            ["n"],
            1,
            1,
            {"new_session"},
            id="n as parameter with parameter and cursor position as 1",
        ),
        pytest.param(
            [""],
            1,
            1,
            {"new_session", "info"},
            id="no parameter with parameter and cursor position as 1",
        ),
        pytest.param(
            ["in"],
            1,
            2,
            {"info"},
            id="i as parameter with parameter position as 1 and cursor position as 2",
        ),
        pytest.param(
            ["i"],
            2,
            1,
            set([]),
            id="t as parameter with parameter position as 2 and cursor position as 1",
        ),
        pytest.param(
            ["magic"],
            1,
            4,
            set([]),
            id="magic as parameter with parameter position as 1 and cursor position as 4",
        ),
    ],
)
def test_do_complete_in_matlab_magic(
    parameters, parameter_pos, cursor_pos, expected_output
):
    magic_object = matlab()
    output = magic_object.do_complete(parameters, parameter_pos, cursor_pos)
    assert expected_output.issubset(set(output))


async def test_new_session_in_matlab_magic_while_already_in_new_session(mocker):
    """
    Test that an appropriate message is displayed when trying to create a new session while already in a new session.

    This test verifies that when a %%matlab magic command with new_session option is executed
    while MATLAB is already assigned to the kernel in a new session, an appropriate error message
    is displayed indicating that the notebook is already linked to a new MATLAB session.
    """
    mock_kernel = mocker.MagicMock()
    mock_kernel.is_matlab_assigned = True
    mock_kernel.is_shared_matlab = False
    output = []
    async for result in handle_new_matlab_session(mock_kernel):
        output.append(result)

    assert output is not None
    assert EXISTING_NEW_SESSION_ERROR in output[0]["value"][0]


async def test_new_session_in_matlab_magic_while_already_in_shared_session(mocker):
    """
    Test that an exception is raised when trying to switch from shared session to new session.

    This test verifies that when a %%matlab magic command with new_session option is executed
    while MATLAB is already assigned to the kernel, an appropriate exception is raised
    with a message indicating that the notebook is already linked to a MATLAB session.
    """
    mock_kernel = mocker.MagicMock()
    mock_kernel.is_matlab_assigned = True
    mock_kernel.is_shared_matlab = True
    with pytest.raises(Exception) as excinfo:
        async for _ in handle_new_matlab_session(mock_kernel):
            pass

    assert "linked to Default MATLAB session" in str(excinfo.value)


async def test_handle_new_matlab_session_success(mocker):
    """
    Test that MATLAB proxy is started correctly when using MATLAB magic command.

    This test verifies that when a %%matlab magic command with new_session option is executed,
    the kernel properly starts the MATLAB proxy, assigns MATLAB to the kernel
    (is_matlab_assigned=True), and sets the shared MATLAB flag to False.
    """
    mock_kernel = mocker.AsyncMock()
    mock_kernel.is_matlab_assigned = False
    output = []
    async for result in handle_new_matlab_session(mock_kernel):
        output.append(result)

    assert output is not None
    mock_kernel.start_matlab_proxy_and_comm_helper.assert_called_once()
    mock_kernel.perform_startup_checks.assert_called_once()
    mock_kernel.cleanup_matlab_proxy.assert_not_called()
    assert mock_kernel.is_matlab_assigned is True
    assert mock_kernel.is_shared_matlab is False
    assert DEDICATED_SESSION_CONFIRMATION_MSG in output[0]["value"][0]


async def test_handle_new_matlab_session_raises_exception(mocker):
    """
    Test that exceptions during MATLAB magic command execution are handled properly.

    This test verifies that when an exception occurs during the startup of the MATLAB proxy
    (triggered by a %%matlab magic command), the kernel properly handles the error and
    maintains the expected state (is_matlab_assigned=False, is_shared_matlab=True).
    """
    mock_kernel = mocker.AsyncMock()
    mock_kernel.is_matlab_assigned = False
    output = []
    with pytest.raises(Exception):
        async for result in handle_new_matlab_session(mock_kernel):
            output.append(result)

        assert output is not None
        mock_kernel.start_matlab_proxy_and_comm_helper.assert_called_once()
        mock_kernel.perform_startup_checks.side_effect = Exception(
            "MATLAB Connection Error"
        )
        mock_kernel.cleanup_matlab_proxy.assert_called_once()
        assert mock_kernel.is_matlab_assigned is False
        assert mock_kernel.is_shared_matlab is True


@pytest.mark.parametrize(
    "shared_matlab_status, expected_output",
    [
        (True, "MATLAB Shared With Other Notebooks: True"),
        (False, "MATLAB Shared With Other Notebooks: False"),
    ],
    ids=["Shared MATLAB", "Non-shared MATLAB"],
)
async def test_get_kernel_info_in_matlab_magic(
    shared_matlab_status, expected_output, mocker
):
    mock_kernel = mocker.MagicMock()
    mock_kernel._get_kernel_info.return_value = {
        "is_shared_matlab": shared_matlab_status,
        "matlab_version": "R2025b",
        "matlab_root_path": "/path/to/matlab",
        "licensing_mode": "existing_license",
    }
    output = []
    async for result in get_kernel_info(mock_kernel):
        output.append(result)
    assert output is not None
    assert expected_output in output[0]["value"][0]
