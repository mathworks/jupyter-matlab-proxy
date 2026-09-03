# Copyright 2026 The MathWorks, Inc.

import base64
import json
from unittest.mock import MagicMock

import pytest
from pathlib import Path
from jupyter_matlab_kernel.comms.labextension.actions import ConvertAction
from jupyter_matlab_kernel.comms.labextension.actions.types import ActionTypes


@pytest.fixture
def mock_kernel(mocker):
    """Create a mock kernel for testing."""
    kernel = mocker.MagicMock()
    kernel.log = mocker.MagicMock()
    kernel.mwi_comm_helper = mocker.MagicMock()
    return kernel


@pytest.fixture
def mock_comm(mocker):
    """Create a mock comm object for testing."""
    return mocker.MagicMock()


@pytest.fixture
def convert_action(mock_kernel):
    """Create a ConvertAction instance for testing."""
    return ConvertAction(mock_kernel)


def _make_png_b64():
    """Create a minimal base64 PNG string for testing."""
    return base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20).decode()


def test_init_sets_kernel_and_log(mock_kernel):
    """Test that initialization sets kernel and log attributes."""
    # Act
    action = ConvertAction(mock_kernel)

    # Assert
    assert action.kernel is mock_kernel
    assert action.log is mock_kernel.log


@pytest.mark.parametrize(
    "version,expected",
    [
        pytest.param("R2025a", True, id="2025a"),
        pytest.param("R2025b", True, id="2025b"),
        pytest.param("R2026a", True, id="2026a"),
        pytest.param("R2024b", False, id="2024b"),
        pytest.param("R2024a", False, id="2024a"),
        pytest.param("R2023b", False, id="2023b"),
        pytest.param(None, False, id="none"),
        pytest.param("", False, id="empty"),
        pytest.param("invalid", False, id="invalid"),
    ],
)
def test_is_matlab_version_25a_or_later(convert_action, version, expected):
    """Test MATLAB version checking for 25a or later."""
    # Act & Assert
    assert convert_action._is_matlab_version_25a_or_later(version) == expected


def test_validate_data(convert_action):
    """Test validate_data raises for invalid data and succeeds for valid data."""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        convert_action.validate_data({})
    assert "ipynbFilePath" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        convert_action.validate_data({"ipynbFilePath": "/path/to/file.ipynb"})
    assert "liveCodeFilePath" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        convert_action.validate_data({"liveCodeFilePath": "/path/to/file.m"})
    assert "ipynbFilePath" in str(exc_info.value)

    convert_action.validate_data(
        {
            "ipynbFilePath": "/path/to/file.ipynb",
            "liveCodeFilePath": "/path/to/file.m",
        }
    )


@pytest.mark.asyncio
async def test_execute_sends_error_on_validation_failure(convert_action, mock_comm):
    """Test that execute sends error response when validation fails."""
    # Act
    await convert_action.execute(mock_comm, {})

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.CONVERT.value
    assert call_args["liveCodeFilePath"] is None
    assert call_args["error"] is not None
    convert_action.log.error.assert_called_once()


@pytest.mark.asyncio
async def test_execute_rejects_pre_25a_version(
    convert_action, mock_comm, mock_kernel, monkeypatch
):
    """Test that execute sends unsupported version error for MATLAB < R2025a."""
    # Arrange
    mock_status = MagicMock()
    mock_status.matlab_version = "R2024b"

    async def _fetch_status():
        return mock_status

    monkeypatch.setattr(
        mock_kernel.mwi_comm_helper,
        "fetch_matlab_proxy_status",
        _fetch_status,
    )

    data = {"ipynbFilePath": "~/notebook.ipynb", "liveCodeFilePath": "notebook.m"}

    # Act
    await convert_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.CONVERT.value
    assert call_args["liveCodeFilePath"] is None
    assert "MATLABVersionUnsupportedForConversionError" in call_args["error"]


@pytest.mark.asyncio
async def test_execute_converts_successfully_25a_or_later(
    convert_action, mock_comm, mock_kernel, monkeypatch, tmp_path
):
    """Test successful conversion for MATLAB R2025a or later."""
    # Arrange
    mock_status = MagicMock()
    mock_status.matlab_version = "R2025a"

    async def _fetch_status():
        return mock_status

    monkeypatch.setattr(
        mock_kernel.mwi_comm_helper,
        "fetch_matlab_proxy_status",
        _fetch_status,
    )

    notebook = {"cells": [{"cell_type": "code", "source": "x = 1;", "outputs": []}]}
    input_path = tmp_path / "notebook.ipynb"
    input_path.write_text(json.dumps(notebook))

    data = {
        "ipynbFilePath": str(input_path),
        "liveCodeFilePath": "notebook.m",
    }

    monkeypatch.setattr(Path, "cwd", staticmethod(lambda: tmp_path))

    # Act
    await convert_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.CONVERT.value
    assert call_args["error"] is None
    assert call_args["liveCodeFilePath"].endswith(".m")

    output_file = Path(call_args["liveCodeFilePath"])
    assert output_file.exists()
    content = output_file.read_text()
    assert "x = 1;" in content


@pytest.mark.asyncio
async def test_execute_sends_error_on_exception(convert_action, mock_comm, monkeypatch):
    """Test that execute sends error response when exception occurs."""
    # Arrange
    error_message = "Connection failed"

    async def _raise(*args, **kwargs):
        raise Exception(error_message)

    monkeypatch.setattr(
        convert_action.kernel.mwi_comm_helper,
        "fetch_matlab_proxy_status",
        _raise,
    )

    data = {"ipynbFilePath": "~/notebook.ipynb", "liveCodeFilePath": "notebook.m"}

    # Act
    await convert_action.execute(mock_comm, data)

    # Assert
    mock_comm.send.assert_called_once()
    call_args = mock_comm.send.call_args[0][0]
    assert call_args["action"] == ActionTypes.CONVERT.value
    assert call_args["liveCodeFilePath"] is None
    assert call_args["error"] == error_message
    convert_action.log.error.assert_called()


@pytest.mark.parametrize(
    "source,expected",
    [
        pytest.param("x = 1;\n", "x = 1;\n", id="string_source"),
        pytest.param(["x = 1;\n", "y = 2;\n"], "x = 1;\ny = 2;\n", id="list_source"),
    ],
)
def test_get_cell_source(convert_action, source, expected):
    """Test that cell source is returned correctly for string and list inputs."""
    # Arrange
    cell = {"source": source}

    # Act
    result = convert_action._get_cell_source(cell)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        pytest.param("<html>", True, id="html_lowercase"),
        pytest.param("<HTML >", True, id="html_uppercase"),
        pytest.param("prefix <html> suffix", True, id="html_embedded"),
        pytest.param("plain text", False, id="plain_text"),
        pytest.param("<p>not html tag</p>", False, id="other_tag"),
    ],
)
def test_contains_html(convert_action, text, expected):
    """Test HTML detection for various inputs."""
    # Act & Assert
    assert convert_action._contains_html(text) is expected


def test_placeholder_output(convert_action):
    """Test that placeholder output has warning dataType."""
    # Act
    result = convert_action._placeholder_output()

    # Assert
    assert result["dataType"] == "warning"
    assert result["outputData"]["text"] == "Please rerun this cell to see output"


@pytest.mark.parametrize(
    "output,expected_data_type",
    [
        pytest.param(
            {"output_type": "stream", "name": "stdout", "text": "ans = 42\n"},
            "text",
            id="stream_stdout",
        ),
        pytest.param(
            {"output_type": "stream", "name": "stdout", "text": ["ans", " = 42\n"]},
            "text",
            id="stream_stdout_list",
        ),
        pytest.param(
            {
                "output_type": "stream",
                "name": "stderr",
                "text": "Error using plot\nNot enough input arguments.",
            },
            "error",
            id="stream_stderr",
        ),
        pytest.param(
            {"output_type": "execute_result", "data": {"text/plain": "x = 42"}},
            "textualVariable",
            id="text_plain_variable",
        ),
        pytest.param(
            {
                "output_type": "execute_result",
                "data": {"text/plain": "   1   2   3\n   4   5   6"},
            },
            "text",
            id="text_plain_non_variable",
        ),
        pytest.param(
            {
                "output_type": "execute_result",
                "data": {"text/plain": "<html><body>table</body></html>"},
            },
            "warning",
            id="text_plain_with_html",
        ),
        pytest.param(
            {
                "output_type": "execute_result",
                "data": {"text/plain": ["result = ", "3.14"]},
            },
            "textualVariable",
            id="text_plain_list",
        ),
        pytest.param(
            {"output_type": "execute_result", "data": {"text/latex": "$x = y + 1$"}},
            "symbolic",
            id="latex",
        ),
        pytest.param(
            {
                "output_type": "execute_result",
                "data": {"text/latex": ["$f", " = x^2 + 1$"]},
            },
            "symbolic",
            id="latex_list",
        ),
        pytest.param(
            {
                "output_type": "execute_result",
                "data": {"text/html": "<div class='table'>data</div>"},
            },
            "warning",
            id="text_html",
        ),
        pytest.param(
            {"output_type": "display_data", "data": {"text/plain": "val = 10"}},
            "textualVariable",
            id="display_data",
        ),
        pytest.param(
            {"output_type": "unknown_type"},
            "warning",
            id="unknown_type",
        ),
    ],
)
def test_classify_output(convert_action, output, expected_data_type):
    """Test that various output types are classified correctly."""
    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["dataType"] == expected_data_type


def test_classify_output_stream_stdout_text_content(convert_action):
    """Test that stdout stream output contains correct text and truncated flag."""
    # Arrange
    output = {"output_type": "stream", "name": "stdout", "text": "ans = 42\n"}

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["outputData"]["text"] == "ans = 42\n"
    assert result["outputData"]["truncated"] is False


def test_classify_output_stream_stderr_content(convert_action):
    """Test that stderr stream output contains errorType and text."""
    # Arrange
    output = {
        "output_type": "stream",
        "name": "stderr",
        "text": "Error using plot\nNot enough input arguments.",
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["outputData"]["errorType"] == "runtime"
    assert (
        result["outputData"]["text"] == "Error using plot\nNot enough input arguments."
    )


def test_classify_output_variable_content(convert_action):
    """Test that textualVariable output contains correct name and value."""
    # Arrange
    output = {
        "output_type": "execute_result",
        "data": {"text/plain": "x = 42"},
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["outputData"]["name"] == "x"
    assert result["outputData"]["value"] == "42"


def test_classify_output_latex_unnamed_content(convert_action):
    """Test that an unnamed (bare-expression) symbolic latex output keeps the
    whole latex body as ``value`` with an empty ``name``.

    The kernel emits unnamed symbolic results as ``$...$`` (leading ``$``).
    _split_symbolic_latex must NOT split on the interior ``=`` in that case,
    otherwise the expression is corrupted (see _split_symbolic_latex docstring).
    """
    # Arrange
    output = {
        "output_type": "execute_result",
        "data": {"text/latex": "$x = y + 1$"},
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["outputData"]["name"] == ""
    assert result["outputData"]["value"] == "$x = y + 1$"


def test_classify_output_latex_named_content(convert_action):
    """Test that a named (assignment) symbolic latex output splits into the
    variable name and the latex body.

    The kernel emits named results as ``<name> =$...$`` (name before the first
    ``$``), which must split on the first `` =`` separator.
    """
    # Arrange
    output = {
        "output_type": "execute_result",
        "data": {"text/latex": "f =$\\displaystyle{}x^2 + 1$"},
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["outputData"]["name"] == "f"
    assert result["outputData"]["value"] == "$\\displaystyle{}x^2 + 1$"


def test_classify_output_image_png(convert_action):
    """Test that image/png output contains dataUri."""
    # Arrange
    b64_data = _make_png_b64()
    output = {
        "output_type": "execute_result",
        "data": {"image/png": b64_data},
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["dataType"] == "image"
    assert result["outputData"]["dataUri"].startswith("data:image/png;base64,")


def test_classify_output_image_png_list(convert_action):
    """Test that image/png as list is joined before classification."""
    # Arrange
    b64_data = _make_png_b64()
    half = len(b64_data) // 2
    output = {
        "output_type": "execute_result",
        "data": {"image/png": [b64_data[:half], b64_data[half:]]},
    }

    # Act
    result = convert_action._classify_output(output)

    # Assert
    assert result["dataType"] == "image"


@pytest.mark.parametrize(
    "obj,assertion",
    [
        pytest.param(
            {"dataType": "text", "outputData": {"text": "path/to/file"}},
            lambda r: "path\\/to\\/file" in r,
            id="escapes_slashes",
        ),
        pytest.param(
            {"dataType": "text", "outputData": {"text": "ans = 5", "truncated": False}},
            lambda r: ": " not in r and ", " not in r,
            id="compact_no_spaces",
        ),
    ],
)
def test_serialize_json(convert_action, obj, assertion):
    """Test that JSON serialization is compact with escaped slashes."""
    # Act
    result = convert_action._serialize_json(obj)

    # Assert
    assert assertion(result)


def test_convert_notebook_code_cell_without_outputs(convert_action):
    """Test converting a notebook with a code cell and no outputs."""
    # Arrange
    notebook = {"cells": [{"cell_type": "code", "source": "x = 1;\n", "outputs": []}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "x = 1;" in result
    assert "%[output:" not in result
    assert '%[appendix]{"version":"1.0"}' in result


def test_convert_notebook_markdown_cell(convert_action):
    """Test that markdown cells are prefixed with %[text]."""
    # Arrange
    notebook = {"cells": [{"cell_type": "markdown", "source": "# Title\nSome text"}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[text] # Title" in result
    assert "%[text] Some text" in result


def test_convert_notebook_raw_cell(convert_action):
    """Test that raw cells are converted to %[text] lines."""
    # Arrange
    notebook = {
        "cells": [{"cell_type": "raw", "source": "\\pagebreak\nsome raw content"}]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[text] \\pagebreak" in result
    assert "%[text] some raw content" in result


def test_convert_notebook_multiple_cells_section_break(convert_action):
    """Test that multiple cells are separated by %% section breaks."""
    # Arrange
    notebook = {
        "cells": [
            {"cell_type": "code", "source": "a = 1;", "outputs": []},
            {"cell_type": "code", "source": "b = 2;", "outputs": []},
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    lines = result.split("\n")
    assert "%%" in lines


def test_convert_notebook_code_cell_with_outputs(convert_action):
    """Test that outputs are included in appendix."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": "disp('hi')",
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": "hi\n",
                    }
                ],
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[output:" in result
    assert "%---" in result


def test_convert_notebook_code_cell_source_list(convert_action):
    """Test that code cell source as list is joined."""
    # Arrange
    notebook = {
        "cells": [{"cell_type": "code", "source": ["a = ", "1;"], "outputs": []}]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "a = 1;" in result


def test_convert_notebook_empty_code_cell(convert_action):
    """Test that empty code cell still produces valid output."""
    # Arrange
    notebook = {"cells": [{"cell_type": "code", "source": "", "outputs": []}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert '%[appendix]{"version":"1.0"}' in result


def test_convert_notebook_appendix_metadata(convert_action):
    """Test that appendix includes metadata view section."""
    # Arrange
    notebook = {"cells": [{"cell_type": "code", "source": "x=1", "outputs": []}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[metadata:view]" in result
    assert '{"layout":"inline"}' in result


def test_convert_notebook_trailing_newline_stripped(convert_action):
    """Test that trailing newline is stripped from code cell source."""
    # Arrange
    notebook = {"cells": [{"cell_type": "code", "source": "x = 1;\n", "outputs": []}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    body = result.split("\n%[appendix]")[0]
    assert body.strip() == "x = 1;"


def test_convert_reads_ipynb_and_writes_m_file(convert_action, tmp_path):
    """Test that _convert reads an ipynb file and writes a .m file."""
    # Arrange
    notebook = {"cells": [{"cell_type": "code", "source": "x = 1;", "outputs": []}]}
    input_path = tmp_path / "test.ipynb"
    output_path = tmp_path / "test.m"
    input_path.write_text(json.dumps(notebook))

    # Act
    convert_action._convert(str(input_path), str(output_path))

    # Assert
    assert output_path.exists()
    content = output_path.read_text()
    assert "x = 1;" in content
    assert '%[appendix]{"version":"1.0"}' in content


def test_convert_with_outputs_included(convert_action, tmp_path):
    """Test that _convert includes outputs in the generated file."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": "disp('hello')",
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": "hello\n",
                    }
                ],
            }
        ]
    }
    input_path = tmp_path / "test.ipynb"
    output_path = tmp_path / "test.m"
    input_path.write_text(json.dumps(notebook))

    # Act
    convert_action._convert(str(input_path), str(output_path))

    # Assert
    content = output_path.read_text()
    assert "%[output:" in content


def test_generate_output_id_format(convert_action):
    """Test that generated output ID is an 8-character hex string."""
    # Act
    oid = convert_action._generate_output_id()

    # Assert
    assert len(oid) == 8
    assert int(oid, 16) is not None


def test_generate_output_id_unique(convert_action):
    """Test that generated output IDs are unique."""
    # Act
    ids = [convert_action._generate_output_id() for _ in range(100)]

    # Assert
    assert len(set(ids)) == 100


@pytest.mark.parametrize(
    "source,expected",
    [
        pytest.param("x = 1;\n", ["x = 1;"], id="strips_trailing_newline"),
        pytest.param("a = 1;\nb = 2;", ["a = 1;", "b = 2;"], id="multiline"),
        pytest.param("", [""], id="empty_string"),
        pytest.param("x = 1;", ["x = 1;"], id="no_trailing_newline"),
    ],
)
def test_split_source_lines(convert_action, source, expected):
    """Test that source is split into lines with trailing empty line removed."""
    # Act
    result = convert_action._split_source_lines(source)

    # Assert
    assert result == expected


def test_build_appendix_no_outputs(convert_action):
    """Test that appendix contains header and metadata when there are no outputs."""
    # Act
    result = convert_action._build_appendix([], [])

    # Assert
    joined = "\n".join(result)
    assert '%[appendix]{"version":"1.0"}' in joined
    assert "%[metadata:view]" in joined
    assert '{"layout":"inline"}' in joined
    assert "%[output:" not in joined


def test_build_appendix_with_outputs(convert_action):
    """Test that appendix includes output sections for each output entry."""
    # Arrange
    outputs_data = [
        (
            "abc12345",
            {"dataType": "text", "outputData": {"text": "ans = 1", "truncated": False}},
        ),
    ]

    # Act
    result = convert_action._build_appendix(outputs_data, [])

    # Assert
    joined = "\n".join(result)
    assert "%[output:abc12345]" in joined
    assert "%   data:" in joined
    assert '"dataType":"text"' in joined


def test_build_appendix_with_media_entries(convert_action):
    """Test that appendix includes media (image/video) sections built from
    markdown conversion appendix entries."""
    # Arrange
    media_entries = [
        (
            "text:image",
            "1abc",
            {"align": "baseline", "height": 200, "src": "data:image/png;base64,AAAA"},
        ),
        (
            "text:video",
            "2def",
            {"height": 315, "vidSrc": "https://youtube.com/embed/x", "width": 560},
        ),
    ]

    # Act
    result = convert_action._build_appendix([], media_entries)

    # Assert
    joined = "\n".join(result)
    assert "%[text:image:1abc]" in joined
    assert "%[text:video:2def]" in joined
    # Slashes in the src/vidSrc must be escaped in the serialized data
    assert "data:image\\/png;base64,AAAA" in joined
    assert "https:\\/\\/youtube.com\\/embed\\/x" in joined


def test_convert_notebook_markdown_cell_with_html(convert_action):
    """Test that HTML in markdown cells is escaped in the output."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "<table>\n<tr><td>hi</td></tr>\n</table>",
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[text] \\<table\\>" in result
    assert "%[text] \\<tr\\>\\<td\\>hi\\</td\\>\\</tr\\>" in result
    assert "%[text] \\</table\\>" in result


def test_convert_notebook_markdown_cell_with_horizontal_rule(convert_action):
    """Test that horizontal rules in markdown cells are escaped."""
    # Arrange
    notebook = {"cells": [{"cell_type": "markdown", "source": "above\n---\nbelow"}]}

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[text] \\---" in result
    assert "%[text] above" in result
    assert "%[text] below" in result


def test_convert_notebook_markdown_cell_with_block_quote(convert_action):
    """Test that block quotes in markdown cells are escaped."""
    # Arrange
    notebook = {
        "cells": [{"cell_type": "markdown", "source": "> Quote\n  > Indented quote"}]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    assert "%[text] \\> Quote" in result
    assert "%[text]   \\> Indented quote" in result


def test_convert_notebook_markdown_table(convert_action):
    """Test that markdown tables are wrapped with %[text:table] markers."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "| Col A | Col B |\n| --- | --- |\n| x | y |",
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    lines = result.split("\n")
    assert '%[text:table]{"ignoreHeader":false}' in lines
    assert "%[text] | Col A | Col B |" in lines
    assert "%[text] | --- | --- |" in lines
    assert "%[text] | x | y |" in lines
    assert "%[text:table]" in lines


def test_convert_notebook_markdown_table_with_surrounding_text(convert_action):
    """Test that table markers don't affect surrounding non-table content."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "Before table\n| A | B |\n| --- | --- |\n| 1 | 2 |\nAfter table",
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    lines = result.split("\n")
    assert "%[text] Before table" in lines
    assert '%[text:table]{"ignoreHeader":false}' in lines
    assert "%[text] | A | B |" in lines
    assert "%[text] | --- | --- |" in lines
    assert "%[text] | 1 | 2 |" in lines
    assert "%[text:table]" in lines
    assert "%[text] After table" in lines


def test_convert_notebook_pipe_lines_without_separator_not_table(convert_action):
    """Test that pipe lines without a separator row are not treated as a table."""
    # Arrange
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "| not a table |\n| also not |",
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    lines = result.split("\n")
    assert '%[text:table]{"ignoreHeader":false}' not in lines
    assert "%[text:table]" not in lines


def test_convert_notebook_table_needs_minimum_three_rows(convert_action):
    """Test that a table needs at least 3 rows (header + separator + data)."""
    # Arrange - only header and separator, no data row
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "| A |\n| --- |",
            }
        ]
    }

    # Act
    result = convert_action._convert_notebook(notebook)

    # Assert
    lines = result.split("\n")
    assert '%[text:table]{"ignoreHeader":false}' not in lines
