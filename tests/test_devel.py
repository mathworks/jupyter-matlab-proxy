# Copyright 2021 The MathWorks, Inc.

import pytest, socket, os, requests, pty, time, subprocess, sys
from pathlib import Path
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
from collections import namedtuple

"""
This file consists of tests which check the devel.py file
"""


@pytest.fixture(name="matlab_port_setup")
def matlab_port_fixture(monkeypatch):
    """A pytest fixture to monkeypatch an environment variable.

    This fixture monkeypatches MW_CONNECTOR_SECURE_PORT env variable which the
    fake matlab server utilizes.

    Args:
        monkeypatch : A built-in pytest fixture.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    matlab_port = s.getsockname()[1]
    s.close()
    monkeypatch.setenv("MW_CONNECTOR_SECURE_PORT", str(matlab_port))


@pytest.fixture(name="valid_nlm")
def valid_nlm_fixture(monkeypatch):
    """A pytest fixture to monkeypatch an environment variable.

    This fixture monkeypatches MLM_LICENSE_FILE with a valid NLM connection string.

    Args:
        monkeypatch : A built-in pytest fixture
    """

    monkeypatch.setenv(mwi_env.get_env_name_network_license_manager(), "abc@nlm")


@pytest.fixture(name="invalid_nlm")
def invalid_nlm_fixture(monkeypatch):
    """A pytest fixture to monkeypatch an environment variable.

    This fixture monkeypatches MLM_LICENSE_FILE with an invalid NLM connection string.


    Args:
        monkeypatch : A built-in pytest fixture
    """

    monkeypatch.setenv(mwi_env.get_env_name_network_license_manager(), "123@brokenhost")


@pytest.fixture(name="matlab_process_setup")
def matlab_process_setup_fixture():
    """A pytest fixture which creates a NamedTuple required for creating a fake matlab process

    This fixture returns a NamedTuple containing values required to run the fake matlab process

    Returns:
        variables : A NamedTuple containing the following values:

            devel_file = Path to devel_file
            matlab_cmd = The matlab command to start the matlab process
            master, slave =  Returns the master, slave file descriptors of returned by pty.openpty() function
    """

    matlab_setup_variables = namedtuple(
        "matlab_setup_variables",
        ["devel_file", "matlab_cmd", "master", "slave"],
    )
    devel_file = Path(os.path.join(os.getcwd(), "jupyter_matlab_proxy", "devel.py"))

    master, slave = pty.openpty()
    python_executable = sys.executable

    matlab_cmd = [
        python_executable,
        "-u",
        str(devel_file),
        "matlab",
        "--ready-delay",
        "0",
    ]
    variables = matlab_setup_variables(devel_file, matlab_cmd, master, slave)

    return variables


@pytest.fixture(name="matlab_process_valid_nlm")
def matlab_process_valid_nlm_fixture(
    matlab_port_setup, matlab_process_setup, valid_nlm
):
    """A pytest fixture which creates a fake matlab process with a valid NLM connection string.

    This  pytest fixture creates a matlab process and yields control to the test which utilizes this
    fixture. After completion of tests stops the matlab process
    """

    matlab_process = subprocess.Popen(
        matlab_process_setup.matlab_cmd,
        stdin=matlab_process_setup.slave,
        stderr=subprocess.PIPE,
    )

    yield

    matlab_process.terminate()
    matlab_process.wait()


def test_matlab_valid_nlm(matlab_process_valid_nlm):
    """Test if the Fake Matlab server has started and is able to serve content.

    This test checks if the fake matlab process is able to start a web server and serve some
    fake content.

    Args:
        matlab_process_valid_nlm : A pytest fixture which creates the fake matlab process which starts the web server

    Raises:
        ConnectionError: If the fake matlab server doesn't startup, after the specified number of max_tries this test
        raises a ConnectionError.
    """

    matlab_port = os.environ["MW_CONNECTOR_SECURE_PORT"]

    url = f"http://localhost:{matlab_port}/index-jsd-cr.html"

    max_tries = 5
    count = 0
    while True:
        try:
            resp = requests.get(url)
            assert resp.status_code == 200
            assert resp.content is not None
            break
        except:
            count += 1
            if count > max_tries:
                raise ConnectionError
            time.sleep(2)


@pytest.fixture(name="matlab_process_invalid_nlm")
def matlab_process_invalid_nlm_fixture(
    matlab_port_setup, matlab_process_setup, invalid_nlm
):
    """A pytest fixture which creates a fake matlab server with an invalid NLM connection string.

    Utilizes matlab_port_setup, matlab_process_setup and invalid_nlm fixtures for creating a
    fake matlab web server then yields control for tests to utilize it.


    Args:
        matlab_port_setup : A pytest fixture which monkeypatches an environment variable.
        matlab_process_setup (NamedTuple): A NamedTuple which contains values to start the matlab process
        invalid_nlm : A pytest fixture which monkeypatches an invalid nlm connection string
    """

    matlab_process = subprocess.Popen(
        matlab_process_setup.matlab_cmd,
        stdin=matlab_process_setup.slave,
        stderr=subprocess.PIPE,
    )

    yield

    matlab_process.terminate()
    matlab_process.wait()


async def test_matlab_invalid_nlm(matlab_process_invalid_nlm):
    """Test which checks if the fake Matlab process stops when NLM string is invalid

    When the NLM string is invalid, the fake matlab server will automatically
    exit. This test checks if a ConnectionError is raised when a GET request is sent to it.

    Args:
        matlab_process_invalid_nlm (Process): A process which starts a fake Matlab WebServer.
    """

    matlab_port = os.environ["MW_CONNECTOR_SECURE_PORT"]
    url = f"http://localhost:{matlab_port}/index-jsd-cr.html"

    with pytest.raises(requests.exceptions.ConnectionError):
        resp = requests.get(url)
