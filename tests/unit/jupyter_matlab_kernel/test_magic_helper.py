# Copyright 2024 The MathWorks, Inc.

from jupyter_matlab_kernel.magic_helper import get_magic_names


def test_get_magic_names():
    output = get_magic_names()
    expected_output = {"lsmagic", "help", "time"}
    assert expected_output.issubset(set(output))


def test_get_magic_names_only_outputs_py_files():
    output = get_magic_names()
    unexpected_output = {"README.md"}
    assert not unexpected_output.issubset(set(output))
