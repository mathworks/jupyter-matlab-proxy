# Copyright 2024 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.magics.time import time
from jupyter_matlab_kernel.mwi_exceptions import MagicError


def test_time_output():
    magic_object = time()
    before_cell_executor = magic_object.before_cell_execute()
    next(before_cell_executor)
    with pytest.raises(Exception):
        next(before_cell_executor)
    after_cell_executor = magic_object.after_cell_execute()
    output = next(after_cell_executor)
    expected_output = "Execution of the cell took"
    assert expected_output in output["value"][0]
    with pytest.raises(Exception):
        next(after_cell_executor)


def test_time_with_parameters():
    magic_object = time(["parameter1"])
    before_cell_executor = magic_object.before_cell_execute()
    with pytest.raises(MagicError):
        next(before_cell_executor)


@pytest.mark.parametrize(
    "seconds, expected",
    [
        pytest.param(3600, "1.00 hours", id="1 hours"),
        pytest.param(3599, "59.98 minutes", id="59.98 minutes"),
        pytest.param(180, "3.00 minutes", id="3 minutes"),
        pytest.param(60, "1.00 minutes", id="1 minute"),
        pytest.param(45, "45.00 seconds", id="45 seconds"),
        pytest.param(1, "1.00 seconds", id="1 second"),
        pytest.param(0.5, "500.00 milliseconds", id="500 milliseconds"),
        pytest.param(0.05, "50.00 milliseconds", id="50 milliseconds"),
        pytest.param(0.001, "1.00 milliseconds", id="1 millisecond"),
        pytest.param(0, "0.00 milliseconds", id="0 milliseconds"),
        pytest.param(0.0005, "0.50 milliseconds", id="0.5 milliseconds"),
    ],
)
def test_time_format_duration(seconds, expected):
    magic_object = time()
    assert magic_object.format_duration(seconds) == expected


if __name__ == "__main__":
    pytest.main()
