# Copyright 2021 The MathWorks, Inc.

import jupyter_matlab_proxy.settings as settings
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
import pytest
import os

"""This file tests methods defined in settings.py file
"""


@pytest.fixture(name="version_info_file_content")
def version_info_file_content_fixture():
    """
    Pytest fixture which returns the contents of a valid VersionInfo.xml file
    """
    return """<!--  Version information for MathWorks R2020b Release  -->
                <MathWorks_version_info>
                <version>9.9.0.1524771</version>
                <release>R2020b</release>
                <description>Update 2</description>
                <date>Nov 03 2020</date>
                <checksum>2207788044</checksum>
                </MathWorks_version_info>
            """


@pytest.fixture(name="fake_matlab_path")
def fake_matlab_path_fixture(tmp_path, version_info_file_content):
    """Pytest fixture to create a fake matlab installation path.


    This fixture creates a fake matlab installation path and creates a valid VersionInfo.xml file.

    Args:
        tmp_path : Built-in pytest fixture
        version_info_file_content : Pytest fixture which returns contents of a valid VersionInfo.xml file.

    Returns:
        Path: A temporary fake matlab installation path
    """

    with open(tmp_path / "VersionInfo.xml", "w") as file:
        file.write(version_info_file_content)

    matlab_path = tmp_path / "bin" / "matlab"
    os.makedirs(matlab_path, exist_ok=True)

    return matlab_path


@pytest.fixture(name="mock_shutil_which_none")
def mock_shutil_which_none_fixture(mocker):
    """Pytest fixture to mock shutil.which() method to return None

    Args:
        mocker : Built in pytest fixture
    """
    mocker.patch("shutil.which", return_value=None)


def test_get_matlab_path_none(mock_shutil_which_none):
    """Test to check if settings.get_matlab_path() returns none when no matlab installation is present.

    mock_shutil_which_none fixture mocks shutil.which() to return None

    Args:
        mock_shutil_which_none : Pytest fixture to mock shutil.which() method to return None.
    """
    assert settings.get_matlab_path() is None


@pytest.fixture(name="mock_shutil_which")
def mock_shutil_which_fixture(mocker, fake_matlab_path):
    """Pytest fixture to mock shutil.which() method to return a temporary fake matlab path

    Args:
        mocker : Built in pytest fixture
        fake_matlab_path : Pytest fixture which returns a temporary fake matlab path.
    """
    mocker.patch("shutil.which", return_value=fake_matlab_path)


def test_get_matlab_path(tmp_path, mock_shutil_which):
    """Test to check if a valid matlab path is returned


    mock_shutil_which fixture mocks shutil.which() method to return a temporary path.

    Args:
        tmp_path : Built in pytest fixture which provides a temporary directory.~
        mock_shutil_which : Pytest fixture to mock shutil.which() method to return a fake matlab path
    """
    assert settings.get_matlab_path() == tmp_path


def test_get_matlab_version_none():
    """Test to check settings.get_matlab_version() returns None when no valid matlab path is provided."""
    assert settings.get_matlab_version(None) is None


def test_get_matlab_version(mock_shutil_which):
    """Test if a matlab version is returned when from a Version.xml file.

    mock_shutil_which fixture will mock the settings.get_matlab_path() to return a fake matlab path
    which containing a valid VersionInfo.xml file. settings.get_matlab_version() will extract the matlab version
    from this file

    Args:
        mock_shutil_which : Pytest fixture to mock shutil.which() method.
    """
    matlab_path = settings.get_matlab_path()
    settings.get_matlab_version(matlab_path) is not None


def test_get_dev_true():
    """Test to check settings returned by settings.get() method in dev mode."""
    dev_mode_settings = settings.get(dev=True)

    assert dev_mode_settings["matlab_cmd"][0] != "matlab"
    assert dev_mode_settings["matlab_protocol"] == "http"


@pytest.fixture(name="patch_env_variables")
def patch_env_variables_fixture(monkeypatch):
    """Pytest fixture to Monkeypatch APP_PORT, BASE_URL, APP_HOST AND MLM_LICENSE_FILE env variables


    Args:
        monkeypatch : Built-in pytest fixture
    """
    monkeypatch.setenv(mwi_env.get_env_name_base_url(), "localhost")
    monkeypatch.setenv(mwi_env.get_env_name_app_port(), "8900")
    monkeypatch.setenv(mwi_env.get_env_name_app_host(), "localhost")
    monkeypatch.setenv(mwi_env.get_env_name_network_license_manager(), "123@nlm")


def test_get_dev_false(patch_env_variables, mock_shutil_which):
    """Test settings.get() method in Non Dev mode.

    In Non dev mode, settings.get() expects APP_PORT, BASE_URL, APP_HOST AND MLM_LICENSE_FILE env variables
    to be present. patch_env_variables monkeypatches them.

    Args:
        patch_env_variables : Pytest fixture which monkeypatches some env variables.
    """
    _settings = settings.get(dev=False)
    assert _settings["matlab_cmd"][0] == "matlab"
    assert os.path.isdir(_settings["matlab_path"])
    assert _settings["matlab_protocol"] == "https"
