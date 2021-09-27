# Copyright 2020-2021 The MathWorks, Inc.

from json.decoder import JSONDecodeError
import pytest, os, time, json, stat
from jupyter_matlab_proxy.util import mwi_custom_http_headers
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env


def test_get_custom_header_env_var():
    """Test to check if the __get_custom_header_env_var() method returns the expected environment variable name"""
    assert (
        mwi_env.get_env_name_custom_http_headers()
        == mwi_custom_http_headers.__get_custom_header_env_var()
    )


def test_get_exception_statement():
    """Test to check if __get_exception_statement() contains 'JSON data' in the generic exception statement returned by __get_exception_statement()"""
    assert "JSON data" in mwi_custom_http_headers.__get_exception_statement()


@pytest.fixture(name="non_existent_temp_json_file")
def non_existent_random_json_file_fixture(tmp_path):
    """Pytest fixture which returns a non-existent random json file within a temporary directory

    Args:
        tmp_path : Built in Pytest fixture.

    Returns:
        PosixPath: of the non-existent random json file.
    """
    random_file = tmp_path / f'{str(time.time()).replace(".", "")}.json'
    return random_file


@pytest.fixture(name="monkeypatch_env_var_with_json_file")
def monkeypatch_env_var_with_json_file_fixture(
    monkeypatch, non_existent_temp_json_file
):
    """Pytest fixture which monkeypatches the env variable returned by the __get_custom_header_env_var()
    method with the value returned by the pytest fixture non_existent_tmp_json_file

    Args:
        monkeypatch : Built in pytest fixture
        non_existent_temp_json_file: Pytest fixture which returns a string containing path
                                        to non-existent file in a temporary directory.
    """
    monkeypatch.setenv(
        mwi_env.get_env_name_custom_http_headers(),
        str(non_existent_temp_json_file),
    )


@pytest.fixture(name="valid_json_content")
def valid_json_content_fixture():
    """Pytest fixture which returns valid JSON data as a string

    Returns:
        [String]: containing valid JSON data.
    """
    return '{"abcd": "hello"}'


@pytest.fixture(name="json_file_with_valid_json")
def json_file_with_valid_json_fixture(non_existent_temp_json_file, valid_json_content):
    """Pytest fixture which returns a random json file containing valid json data

    Args:
        non_existent_temp_json_file : Pytest fixture which returns a non-existent random json file.
        valid_json_content : Pytest fixture which returns valid JSON data as a string.

    Returns:
        [PosixPath]: Of a random json file containing valid json data.
    """
    json_file_with_valid_content = non_existent_temp_json_file
    with open(json_file_with_valid_content, "w") as f:
        f.write(valid_json_content)

    return json_file_with_valid_content


def test_get_file_contents_with_valid_json(json_file_with_valid_json):
    """Test to check if __get_file_contents() returns valid json data as a dict from a file

    Args:
        json_file_with_valid_json : Pytest fixture which returns a non-existent random json file.
    """
    file_content = None
    with open(json_file_with_valid_json, "r") as f:
        file_content = json.load(f)

    assert file_content == mwi_custom_http_headers.__get_file_contents(
        json_file_with_valid_json
    )


@pytest.fixture(name="invalid_json_content")
def invalid_json_content_fixture():
    """Pytest fixture which returns invalid json data as a string

    Returns:
        [String]: containing invalid json data.
    """
    return '{"abcd"= "hello"}'


@pytest.fixture(name="json_file_with_invalid_json")
def json_file_with_invalid_json_fixture(
    non_existent_temp_json_file, invalid_json_content
):
    """Pytest fixture which returns a path to a random json file containing invalid json data.

    Args:
        non_existent_temp_json_file : Pytest fixture which returns a non-existent random json file.
        invalid_json_content : Pytest fixture which returns invalid json data as a string.

    Returns:
        PosixPath: to a random file containing invalid json data.
    """
    json_file_with_invalid_content = non_existent_temp_json_file
    with open(json_file_with_invalid_content, "w") as f:
        f.write(invalid_json_content)

    return json_file_with_invalid_content


def test_get_file_contents_with_invalid_json(json_file_with_invalid_json, capsys):
    """Test to check __get_file_contents() raises JSONDecodeError when invalid json data is present in a file.

    Args:
        json_file_with_invalid_json : Pytest fixture which returns a non-existent random json file.
    """
    with pytest.raises(SystemExit):
        mwi_custom_http_headers.__get_file_contents(json_file_with_invalid_json)
        out, err = capsys.readouterr()
        assert JSONDecodeError.__name__ in out


def test_check_file_validity_no_read_access(non_existent_temp_json_file, capsys):
    """Test to check if OSError is raised when trying to read file with no read access.

    Args:
        non_existent_temp_json_file : Pytest fixture which returns a non-existent random json file.
    """
    temp_json_file_no_read_access = non_existent_temp_json_file
    temp_json_file_no_read_access.touch(mode=stat.S_IWUSR)

    with pytest.raises(SystemExit):
        mwi_custom_http_headers.__check_file_validity(temp_json_file_no_read_access)
        out, err = capsys.readouterr()
        assert OSError.__name__ in out


def test_check_file_validity_no_error(non_existent_temp_json_file, valid_json_content):
    """Test to check __check_file_validity() does not raise any exception when the custom headers file
    exists, has valid JSON data and the current python process has read access to the file.

    Args:
        non_existent_temp_json_file : Pytest fixture which returns a non-existent random json file.
    """

    random_json_file_with_valid_content = non_existent_temp_json_file
    with open(random_json_file_with_valid_content, "w") as f:
        f.write(valid_json_content)

    assert (
        mwi_custom_http_headers.__check_file_validity(
            random_json_file_with_valid_content
        )
        is True
    )


def test_get_no_env_var():
    """Test to check if get() returns an empty dict, when mwi_custom_http_headers env variable is not present."""
    assert mwi_custom_http_headers.get() == dict()


def test_get_with_json_file_no_error(
    monkeypatch_env_var_with_json_file, valid_json_content
):
    """Test to check if expected json content is returned by get() as a dict when the
    environment variable returned by __get_custom_header_env_var() contains a path to a JSON file

    Args:
        monkeypatch_env_var_with_json_file : Pytest fixture which monkeypatches the env variable returned by __get_custom_header_env_var() to
                              have a non-existent temporary json file.
        valid_json_content : Pytest fixture which returns valid json data as a string.
    """
    tmp_file_path = os.getenv(mwi_env.get_env_name_custom_http_headers())

    with open(tmp_file_path, "w") as f:
        f.write(valid_json_content)

    assert mwi_custom_http_headers.get() == json.loads(valid_json_content)


def test_get_with_json_file_raise_exception(
    monkeypatch_env_var_with_json_file, invalid_json_content, capsys
):
    """Test to check if the get() method raises SystemExit exception when the environment variable returned by __get_custom_env_var()
    contains path to a file with invalid JSON data. Also asserts for JSONDecodeError in stdout.

    Args:
        monkeypatch_env_var_with_json_file : Pytest fixture which monkeypatches the env variable returned by __get_custom_header_env_var() to
                              have a non-existent temporary json file.
        invalid_json_content : Pytest fixture which returns invalid json data as a string.
    """
    tmp_file_path = os.getenv(mwi_env.get_env_name_custom_http_headers())

    with open(tmp_file_path, "w") as f:
        f.write(invalid_json_content)

    with pytest.raises(SystemExit):
        mwi_custom_http_headers.get()
        out, err = capsys.readouterr()
        assert JSONDecodeError.__name__ in out


@pytest.fixture(name="monkeypatch_env_var_with_invalid_json_string")
def monkeypatch_env_var_with_invalid_json_string_fixture(
    monkeypatch, invalid_json_content
):
    """Pytest fixture which monkeypatches the env variable returned by the __get_custom_header_env_var()
    method with the value returned by the pytest fixture non_existent_temp_json_file

    Args:
        monkeypatch : Built in pytest fixture
        non_existent_temp_json_file: Pytest fixture which returns a string containing path
                                        to non-existent file in a temporary directory.
    """
    monkeypatch.setenv(mwi_env.get_env_name_custom_http_headers(), invalid_json_content)


def test_get_with_invalid_json_string(
    monkeypatch_env_var_with_invalid_json_string, capsys
):
    """Test to check if the get() method raises SystemExit exception when the environment variable returned by __get_custom_env_var()
    contains invalid JSON data as a string. Also asserts for JSONDecodeError in stdout.

    Args:
        monkeypatch_env_var_with_invalid_json_string : Pytest fixture which monkeypatches the env variable returned by __get_custom_header_env_var() to
                                                     contain invalid JSON data as a string.
    """
    with pytest.raises(SystemExit):
        headers = mwi_custom_http_headers.get()
        out, err = capsys.readouterr()
        assert JSONDecodeError.__name__ in out


@pytest.fixture(name="monkeypatch_env_var_with_valid_json_string")
def monkeypatch_env_var_with_valid_json_string_fixture(monkeypatch, valid_json_content):
    """Pytest fixture which monkeypatches the env variable returned by the __get_custom_header_env_var()
    method with the value returned by the pytest fixture non_existent_tmp_json_file

    Args:
        monkeypatch : Built in pytest fixture
        non_existent_temp_json_file: Pytest fixture which returns a string containing path
                                        to non-existent file in a temporary directory.
    """
    monkeypatch.setenv(mwi_env.get_env_name_custom_http_headers(), valid_json_content)


def test_get_with_valid_json_string(monkeypatch_env_var_with_valid_json_string):
    """Test to check if expected json content is returned by get() as a dict when the
    environment variable contains valid JSON data as a string

    Args:
        monkeypatch_env_var_with_valid_json_string : Pytest fixture which monkeypatches the env variable returned by __get_custom_header_env_var() to
                                                     contain valid JSON data as a string.
    """
    headers = json.loads(os.getenv(mwi_env.get_env_name_custom_http_headers()))
    assert headers == mwi_custom_http_headers.get()
