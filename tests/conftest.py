# Copyright 2020 The MathWorks, Inc.

import os


def pytest_generate_tests(metafunc):
    os.environ["DEV"] = "true"
