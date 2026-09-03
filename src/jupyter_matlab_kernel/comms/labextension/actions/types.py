# Copyright 2026 The MathWorks, Inc.

from enum import Enum


class ActionTypes(Enum):
    CONVERT = "convert"
    EDIT = "edit"
    MATLAB_STATUS = "matlab_status"
    START_MATLAB_PROXY = "start_matlab_proxy"
    CHECK_FILE_EXISTS = "check_file_exists"
    UNKNOWN = "unknown"  # Fallback action.
