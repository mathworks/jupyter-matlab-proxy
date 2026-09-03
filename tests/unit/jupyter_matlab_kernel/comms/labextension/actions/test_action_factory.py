# Copyright 2026 The MathWorks, Inc.

import pytest
from jupyter_matlab_kernel.comms.labextension.actions import (
    ActionFactory,
    ConvertAction,
    EditAction,
    MatlabStatusAction,
    StartMatlabProxyAction,
    CheckFileExistsAction,
    UnknownAction,
)
from jupyter_matlab_kernel.comms.labextension.actions.types import ActionTypes


@pytest.fixture
def mock_kernel(mocker):
    """Create a mock kernel for testing."""
    kernel = mocker.MagicMock()
    kernel.log = mocker.MagicMock()
    return kernel


@pytest.mark.parametrize(
    "action_type,expected_class",
    [
        (ActionTypes.CONVERT.value, ConvertAction),
        (ActionTypes.EDIT.value, EditAction),
        (ActionTypes.MATLAB_STATUS.value, MatlabStatusAction),
        (ActionTypes.START_MATLAB_PROXY.value, StartMatlabProxyAction),
        (ActionTypes.CHECK_FILE_EXISTS.value, CheckFileExistsAction),
        ("invalid_action_type", UnknownAction),
        (None, UnknownAction),
        ("", UnknownAction),
    ],
)
def test_create_action_returns_correct_type(mock_kernel, action_type, expected_class):
    """Test that ActionFactory.create_action returns the correct action type."""
    action = ActionFactory.create_action(action_type, mock_kernel)
    assert isinstance(action, expected_class)
    assert action.kernel is mock_kernel
