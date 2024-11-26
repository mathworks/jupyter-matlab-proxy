# Copyright 2024 The MathWorks, Inc.

"""
MATLAB plugin that installs MATLAB, its dependencies and the MATLAB Integration for Jupyter
"""

from tljh.hooks import hookimpl
from . import install_matlab


@hookimpl
def tljh_extra_user_pip_packages():
    return ["jupyter-matlab-proxy"]


@hookimpl
def tljh_post_install():
    """
    Post install script to be executed after installation
    and after all the other hooks.

    This can be arbitrary Python code.
    """
    install_matlab.install_matlab_impl()
