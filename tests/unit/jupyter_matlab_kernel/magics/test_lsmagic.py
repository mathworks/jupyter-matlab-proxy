# Copyright 2024 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.magics.lsmagic import lsmagic
from jupyter_matlab_kernel.mwi_exceptions import MagicError


def test_lsmagic_output():
    magic_object = lsmagic()
    before_cell_executor = magic_object.before_cell_execute()
    output = next(before_cell_executor)
    expected_outputs = ["Available magic commands:", "%%lsmagic", "%%help"]
    assert all(
        expected_output in output["value"][0] for expected_output in expected_outputs
    )
    with pytest.raises(Exception):
        next(before_cell_executor)


def test_lsmagic_with_parameters():
    magic_object = lsmagic(["parameter1"])
    before_cell_executor = magic_object.before_cell_execute()
    with pytest.raises(MagicError):
        next(before_cell_executor)
