# Copyright 2020 The MathWorks, Inc.
import sys


def is_python_version_newer_than_3_6():
    """Returns True if the python version being used is 3.7 or higher, else False.

    Returns:
        Boolean: True if python version >= 3.7, False otherwise.
    """
    return sys.version_info[:2] >= (3, 7)
