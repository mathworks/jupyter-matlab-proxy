# Copyright 2020-2021 The MathWorks, Inc.
"""Functions to related to embedded connector access and configuration"""

from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
from jupyter_matlab_proxy import settings as mwi_settings
from pathlib import Path

# TODO Write tests


def get_matlab_ready_file(connector_port):
    """Returns the name and location of the file that is used by MATLAB
    embedded connector to signal its readiness to begin serving content"""
    ready_file_dir = __create_folder_to_hold_matlab_ready_file(connector_port)
    ready_file = ready_file_dir / "connector.securePort"
    return ready_file, ready_file_dir


def __create_folder_to_hold_matlab_ready_file(connector_port):
    """MWI creates the location into which the spawned MATLAB connector can create the ready file"""

    if mwi_env.is_development_mode_enabled():
        return mwi_settings.get_test_temp_dir()

    matlab_tempdir = Path(mwi_settings.get_matlab_tempdir())
    matlab_ready_file_dir = matlab_tempdir / "MWI" / str(connector_port)
    matlab_ready_file_dir.mkdir(parents=True, exist_ok=True)
    return matlab_ready_file_dir
