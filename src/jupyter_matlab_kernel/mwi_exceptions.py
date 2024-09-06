# Copyright 2024 The MathWorks, Inc.
# Custom Exceptions used in MATLAB Kernel


class MagicError(Exception):
    """Custom exception for errors inside magic class

    Args:
        message (string): Error message to be displayed
    """

    def __init__(self, message=None):
        if message is None:
            message = "An uncaught error occurred during magic execution."
        super().__init__(message)


class MagicExecutionEngineError(Exception):
    """Custom exception for error in Magic Execution Engine.

    Args:
        message (string): Error message to be displayed
    """

    def __init__(self, message=None):
        if message is None:
            message = "An uncaught error occurred in the Magic Execution Engine."
        super().__init__(message)


class MATLABConnectionError(Exception):
    """
    A connection error occurred while connecting to MATLAB.

    Args:
        message (string): Error message to be displayed
    """

    def __init__(self, message=None):
        if message is None:
            message = 'Error connecting to MATLAB. Check the status of MATLAB by clicking the "Open MATLAB" button. Retry after ensuring MATLAB is running successfully'
        super().__init__(message)
