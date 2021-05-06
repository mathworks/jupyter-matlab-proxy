# Copyright 2020-2021 The MathWorks, Inc.

import os, pytest, signal, psutil
from jupyter_matlab_proxy import settings
from subprocess import Popen, PIPE


def pytest_generate_tests(metafunc):
    os.environ["DEV"] = "true"


@pytest.fixture(autouse=True, scope="session")
def pre_test_cleanup():
    """A pytest fixture which deletes matlab_config_file before executing tests.

    If a previous pytest run fails, this file may have an empty Dict which leads
    to the server never starting up matlab.
    """

    try:
        matlab_config_file = settings.get(dev=True)["matlab_config_file"]
        os.remove(matlab_config_file)
    except:
        pass
