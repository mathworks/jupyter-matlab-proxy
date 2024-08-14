# Copyright 2024 The MathWorks, Inc.

import os
import pytest

from jupyter_matlab_kernel.magics.file import file
from jupyter_matlab_kernel.mwi_exceptions import MagicError


@pytest.fixture
def temp_dir(tmp_path):
    yield tmp_path


@pytest.mark.parametrize(
    "parameters, cell_code",
    [
        pytest.param(
            [], "%%file\nsome_code", id="no parameters and non-empty cell_code"
        ),
        pytest.param(
            ["myfunc1.m", "myfunc2.m"],
            "%%file myfunc1.m myfunc2.m\nsome_code",
            id="2 parameters and non-empty cell_code",
        ),
        pytest.param(
            ["myfunc1.m"], "%%file myfunc1.m", id="1 parameters and empty cell_code"
        ),
    ],
)
def test_exceptions_in_file_magic(parameters, cell_code, temp_dir):
    parameters = [temp_dir / s for s in parameters]
    magic_object = file(parameters, cell_code)
    before_cell_executor = magic_object.before_cell_execute()
    with pytest.raises(MagicError):
        next(before_cell_executor)
    with pytest.raises(Exception):
        next(before_cell_executor)


def test_file_creation(temp_dir):
    file_path = temp_dir / "myfunc1.m"
    magic_object = file([file_path], "%%file myfunc1.m\nmycode")
    before_cell_executor = magic_object.before_cell_execute()
    output = next(before_cell_executor)
    expected_output = "myfunc1.m created successfully."
    assert expected_output in output["value"][0]
    assert os.path.exists(file_path), f"File {file_path} does not exist."
    with pytest.raises(Exception):
        next(before_cell_executor)
