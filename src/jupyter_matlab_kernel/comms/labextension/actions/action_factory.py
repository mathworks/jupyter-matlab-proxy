# Copyright 2026 The MathWorks, Inc.

from typing import Union
from jupyter_matlab_kernel.comms.labextension.actions import (
    ConvertAction,
    EditAction,
    MatlabStatusAction,
    StartMatlabProxyAction,
    CheckFileExistsAction,
    UnknownAction,
)
from jupyter_matlab_kernel.comms.labextension.actions.types import ActionTypes


class ActionFactory:
    """
    ActionFactory class for determining and returning the appropriate Action class.

    This class provides a static method to decide between different Action
    implementations based on the supplied Action Type.
    """

    @staticmethod
    def create_action(action_type, kernel) -> Union[
        ConvertAction,
        EditAction,
        MatlabStatusAction,
        StartMatlabProxyAction,
        CheckFileExistsAction,
        UnknownAction,
    ]:
        """Determines and returns the appropriate Action to use

        Args:
            action_type (ActionTypes): Type of the action
            kernel (BaseMATLABKernel): The MATLAB Kernel being used

        Returns:
            Union[ConvertAction, EditAction, MatlabStatusAction, StartMatlabProxyAction, UnknownAction]: The appropriate Action class based on the provided action_type.
        """
        if ActionTypes.CONVERT.value == action_type:
            return ConvertAction(kernel)

        elif ActionTypes.EDIT.value == action_type:
            return EditAction(kernel)

        elif ActionTypes.MATLAB_STATUS.value == action_type:
            return MatlabStatusAction(kernel)

        elif ActionTypes.START_MATLAB_PROXY.value == action_type:
            return StartMatlabProxyAction(kernel)

        # Add more elif conditions as and when new action types are introduced
        elif ActionTypes.CHECK_FILE_EXISTS.value == action_type:
            return CheckFileExistsAction(kernel)

        else:
            return UnknownAction(kernel)
