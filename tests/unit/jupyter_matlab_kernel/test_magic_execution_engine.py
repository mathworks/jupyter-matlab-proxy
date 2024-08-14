# Copyright 2024 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.magic_execution_engine import (
    MagicExecutionEngine,
    get_completion_result_for_magics,
)

from jupyter_matlab_kernel.mwi_exceptions import MagicExecutionEngineError


@pytest.mark.parametrize(
    "cell_code, skip_cell_execution",
    [
        pytest.param(
            "%%lsmagic",
            True,
            id="magic command without any MATLAB code does not require cell execution",
        ),
        pytest.param(
            "%%lsmagic\n%%help lsmagic",
            True,
            id="magic commands without any MATLAB code does not require cell execution",
        ),
        pytest.param(
            "%%lsmagic\na=1",
            False,
            id="magic command with MATLAB code requires cell execution",
        ),
        pytest.param(
            "%% not_magic", False, id="Section creator requires cell execution"
        ),
        pytest.param("%#", False, id="Special commands requires cell execution"),
        pytest.param(
            "% This is a comment", False, id="A comment also triggers cell execution"
        ),
        pytest.param(
            "%! Some special command",
            False,
            id="Special command followed by some line requires cell execution",
        ),
        pytest.param("%%", False, id="Only two percent signs require cell execution"),
        pytest.param(
            "%% ",
            False,
            id="Two percent signs followed by a whitespace require cell execution",
        ),
        pytest.param(
            "%Some code",
            False,
            id="Percent directly followed by character requires cell execution",
        ),
    ],
)
def test_cell_code_which_can_trigger_matlab_execution(cell_code, skip_cell_execution):
    magic_executor = MagicExecutionEngine()
    process_before_cell_execution = magic_executor.process_before_cell_execution(
        cell_code, 1
    )
    for output in process_before_cell_execution:
        assert isinstance(output, dict)
    assert magic_executor.skip_cell_execution() is skip_cell_execution


@pytest.mark.parametrize(
    "cell_code",
    [
        pytest.param("%%lsmagic\na=1", id="correct magic definition no error"),
        pytest.param(
            "%%lsmagic\n%%time\na=1",
            id="consecutive magic commands on top of the cell no error",
        ),
        pytest.param(
            "a=1\n%%lsmagic",
            id="magic not on top of the cell should not error and be treated as comments",
        ),
        pytest.param(
            "%%lsmagic\na=1\n%%time",
            id="magic followed by MATLAB code followed by magic should not error as the second magic is treated as a comment",
        ),
    ],
)
def test_correct_magic_definition(cell_code):
    magic_executor = MagicExecutionEngine()
    process_before_cell_execution = magic_executor.process_before_cell_execution(
        cell_code, 1
    )
    process_after_cell_execution = magic_executor.process_after_cell_execution()
    for output in process_before_cell_execution:
        assert isinstance(output, dict)
    for output in process_after_cell_execution:
        assert isinstance(output, dict)


@pytest.mark.parametrize(
    "cell_code",
    [
        pytest.param("%%mymagic", id="invalid magic should error"),
        pytest.param("%%lsmagic help", id="magic with invalid parameter should error"),
    ],
)
def test_incorrect_magic_definition(cell_code):
    magic_executor = MagicExecutionEngine()
    process_before_cell_execution = magic_executor.process_before_cell_execution(
        cell_code, 1
    )
    process_after_cell_execution = magic_executor.process_after_cell_execution()
    with pytest.raises(MagicExecutionEngineError):
        for output in process_before_cell_execution:
            assert isinstance(output, dict)
        for output in process_after_cell_execution:
            assert isinstance(output, dict)


@pytest.mark.parametrize(
    "cell_code, cursor_pos, expected_output, expected_start, expected_end",
    [
        pytest.param(
            "%%",
            2,
            {"lsmagic", "help", "time", "file"},
            2,
            2,
            id="Two percentage without whitespace suggests all magic commands",
        ),
        pytest.param("%%ls", 3, {"lsmagic"}, 2, 3, id="%%ls suggests lsmagic"),
        pytest.param(
            "%%lsmagi",
            4,
            {"lsmagic"},
            2,
            4,
            id="%%lsmagi at cursor postion 4 replaces lsmagic from 2nd position to 4th position",
        ),
        pytest.param(
            " %%",
            3,
            {"lsmagic", "help", "time", "file"},
            3,
            3,
            id="%% preceeded by whitespace suggests all magic commands",
        ),
        pytest.param(
            "%%help ",
            7,
            {"lsmagic", "help", "time", "file"},
            7,
            7,
            id="completion request after magic commands are passed to respective magic functions",
        ),
        pytest.param(
            "%%help    ",
            10,
            {"lsmagic", "help", "time", "file"},
            10,
            10,
            id="whitespace after a valid magic command does not affect the completion result",
        ),
        pytest.param(
            "%%lsmagic",
            9,
            {"lsmagic"},
            2,
            9,
            id="complete magic name still suggests the magic name for completion",
        ),
        pytest.param(
            "%%lsmagic ",
            10,
            set([]),
            10,
            10,
            id="completion request after magic commands returns empty matches",
        ),
        pytest.param(
            "%%lsmagic abc",
            13,
            set([]),
            10,
            13,
            id="parameter completion request in magic parameters returns empty matches",
        ),
        pytest.param(
            "%%fakemagic a",
            13,
            set([]),
            12,
            13,
            id="parameter completion request for invalid magic command returns empty matches",
        ),
    ],
)
def test_get_completion_result_for_magics(
    cell_code, cursor_pos, expected_output, expected_start, expected_end
):
    output = get_completion_result_for_magics(cell_code, cursor_pos)
    assert expected_output.issubset(set(output["matches"]))
    assert expected_start == output["start"]
    assert expected_end == output["end"]


@pytest.mark.parametrize(
    "cell_code, cursor_pos",
    [
        pytest.param("%", 1, id="single percent treated as comment returns None"),
        pytest.param(
            "a=1\n%%h",
            7,
            id=" don't shows suggestions if preceded by MATLAB code",
        ),
        pytest.param("pea", 3, id="MATLAB code so return None"),
        pytest.param("%% l", 4, id="Section creator should return None"),
        pytest.param(
            "%% ",
            3,
            id="%% followed by a whitespace are considered Section creators. Return None",
        ),
    ],
)
def test_no_output_in_get_completion_result_for_magics(cell_code, cursor_pos):
    output = get_completion_result_for_magics(cell_code, cursor_pos)
    assert output is None
