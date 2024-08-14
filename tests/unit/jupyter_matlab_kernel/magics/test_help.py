# Copyright 2024 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.magics.help import help
from jupyter_matlab_kernel.mwi_exceptions import MagicError


def test_help_magic():
    magic_object = help(["lsmagic"])
    before_cell_executor = magic_object.before_cell_execute()
    output = next(before_cell_executor)
    expected_output = "List available magic commands."
    assert expected_output in output["value"][0]


@pytest.mark.parametrize(
    "parameters",
    [
        pytest.param([], id="no magic name should throw exception"),
        pytest.param(
            ["fakemagic"],
            id="magic which does not exist should throw exception",
        ),
        pytest.param(
            ["lsmagic", "help"],
            id="more than one parameter should throw exception",
        ),
    ],
)
def test_help_magic_exceptions(parameters):
    magic_object = help(parameters)
    before_cell_executor = magic_object.before_cell_execute()
    with pytest.raises(MagicError):
        next(before_cell_executor)


@pytest.mark.parametrize(
    "parameters, parameter_pos, cursor_pos, expected_output",
    [
        pytest.param(
            ["ls"],
            1,
            1,
            {"lsmagic"},
            id="ls as parameter with parameter and cursor position as 1",
        ),
        pytest.param(
            [""],
            1,
            1,
            {"lsmagic", "help", "file", "time"},
            id="no parameter with parameter and cursor position as 1",
        ),
        pytest.param(
            ["t"],
            2,
            1,
            set([]),
            id="t as parameter with parameter position as 2 and cursor position as 1",
        ),
        pytest.param(
            ["magic"],
            1,
            4,
            set([]),
            id="magic as parameter with parameter position as 1 and cursor position as 4",
        ),
    ],
)
def test_do_complete_in_help_magic(
    parameters, parameter_pos, cursor_pos, expected_output
):
    magic_object = help()
    output = magic_object.do_complete(parameters, parameter_pos, cursor_pos)
    assert expected_output.issubset(set(output))
