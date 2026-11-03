# Copyright 2026 The MathWorks, Inc.

import pytest
from unittest.mock import AsyncMock, MagicMock

from jupyter_matlab_kernel.outputs.processor import OutputProcessor
from jupyter_matlab_kernel.outputs.types import (
    FigureOutput,
    FigurePlaceholderOutput,
    HtmlResultOutput,
    LatexResultOutput,
    MarkdownResultOutput,
    StdoutOutput,
    StderrOutput,
)


async def _as_async_iter(*items):
    """Helper to wrap items into an async iterable for testing."""
    for item in items:
        yield item


# ---- Matrix Tests ----


@pytest.mark.asyncio
async def test_output_processor_matrix():
    processor = OutputProcessor()

    out = {
        "type": "matrix",
        "outputData": {
            "name": "ans",
            "header": "5x1",
            "type": "double",
            "value": "1\n2\n3\n4\n5",
            "rows": 5,
            "columns": 1,
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    assert result.msg_type == "execute_result"
    content = result.to_content()
    assert "text/html" in content["data"]
    assert "text/plain" in content["data"]
    assert "ans = 5x1 double" in content["data"]["text/html"]
    assert "<html><pre>" in content["data"]["text/html"]
    assert "ans = 5x1 double" in content["data"]["text/plain"]
    assert "<html><pre>" not in content["data"]["text/plain"]


@pytest.mark.asyncio
async def test_output_processor_matrix_truncation():
    processor = OutputProcessor()

    out = {
        "type": "matrix",
        "outputData": {
            "name": "M",
            "header": "15x1",
            "type": "double",
            "value": "1\n2\n3",
            "rows": 15,
            "columns": 1,
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    content = result.to_content()
    assert content["data"]["text/html"].endswith("...</pre></html>")
    assert content["data"]["text/plain"].endswith("...")


# ---- Variable Tests ----


@pytest.mark.asyncio
async def test_output_processor_variable():
    processor = OutputProcessor()

    out = {
        "type": "variable",
        "outputData": {"name": "x", "header": "", "value": "42"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert content["data"]["text/html"] == "<html><pre>x = 42</pre></html>"
    assert content["data"]["text/plain"] == "x = 42"


@pytest.mark.asyncio
async def test_output_processor_variable_with_header():
    processor = OutputProcessor()

    out = {
        "type": "variable",
        "outputData": {
            "name": "s",
            "header": "struct with fields:",
            "value": "a: 1",
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    content = result.to_content()
    assert (
        content["data"]["text/html"]
        == "<html><pre>s = struct with fields:\n    a: 1</pre></html>"
    )
    assert content["data"]["text/plain"] == "s = struct with fields:\n    a: 1"


@pytest.mark.asyncio
async def test_output_processor_variable_html_escaping():
    processor = OutputProcessor()

    out = {
        "type": "variable",
        "outputData": {"name": "x", "header": "", "value": "<table>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    content = result.to_content()
    assert content["data"]["text/html"] == "<html><pre>x = <table></pre></html>"
    assert content["data"]["text/plain"] == "x = <table>"


# ---- VariableString Tests ----


@pytest.mark.asyncio
async def test_output_processor_variable_string():
    processor = OutputProcessor()

    out = {
        "type": "variableString",
        "outputData": {"name": "str", "header": "", "value": "hello"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert content["data"]["text/html"] == "<html><pre>str = hello</pre></html>"
    assert content["data"]["text/plain"] == "str = hello"


@pytest.mark.asyncio
async def test_output_processor_variable_string_multiline():
    processor = OutputProcessor()

    out = {
        "type": "variableString",
        "outputData": {"name": "str", "header": "", "value": "line1\nline2"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    content = result.to_content()
    assert (
        content["data"]["text/html"] == "<html><pre>str = \nline1\nline2</pre></html>"
    )
    assert content["data"]["text/plain"] == "str = \nline1\nline2"


# ---- Stream Tests (text, warning, stderr) ----


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "out_type, expected_class",
    [
        ("text", StdoutOutput),
        ("warning", StderrOutput),
        ("stderr", StderrOutput),
        ("error", StderrOutput),
    ],
)
async def test_output_processor_stream(out_type, expected_class):
    processor = OutputProcessor()

    out = {"type": out_type, "outputData": {"text": "some output"}}

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, expected_class)
    assert result.msg_type == "stream"
    assert result.to_content()["text"] == "some output"


# ---- Symbolic Tests ----


@pytest.mark.asyncio
async def test_output_processor_symbolic_direct_latex_named():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock()
    mock_logger = MagicMock()
    processor = OutputProcessor(mwi_comm_helper=mock_helper, logger=mock_logger)

    out = {
        "type": "symbolic",
        "outputData": {
            "name": "f",
            "value": "<mathml>...</mathml>",
            "latex": r"\frac{x^2+1}{x+2}",
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    assert result.msg_type == "execute_result"
    assert (
        result.to_content()["data"]["text/latex"]
        == r"f =$\\\ \displaystyle{}\frac{x^2+1}{x+2}$"
    )
    mock_helper.convert_mathml_to_latex.assert_not_awaited()
    mock_logger.debug.assert_any_call(
        "Using direct LaTeX from symbolic output received from MATLAB"
    )


@pytest.mark.asyncio
async def test_output_processor_symbolic_direct_latex_unnamed():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock()
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {
            "name": "",
            "value": "<mathml>...</mathml>",
            "latex": r"\frac{1}{3}",
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    assert result.to_content()["data"]["text/latex"] == r"$\displaystyle{}\frac{1}{3}$"
    mock_helper.convert_mathml_to_latex.assert_not_awaited()


@pytest.mark.asyncio
async def test_output_processor_symbolic_direct_latex_preserves_multiline_body():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value="")
    processor = OutputProcessor(mwi_comm_helper=mock_helper)
    latex_body = (
        "\n  \\begin{array}{l}\n"
        "x^2+y^2 \\\\\n"
        "\\text{where} \\quad x>0\n"
        "\\end{array}  \n"
    )

    direct_out = {
        "type": "symbolic",
        "outputData": {
            "name": "f",
            "value": "<mathml>...</mathml>",
            "latex": latex_body,
        },
    }

    results = [r async for r in processor.process(_as_async_iter(direct_out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    assert (
        result.to_content()["data"]["text/latex"]
        == f"f =$\\\\\\ \\displaystyle{{}}{latex_body}$"
    )
    mock_helper.convert_mathml_to_latex.assert_not_awaited()


@pytest.mark.asyncio
async def test_output_processor_symbolic_multiple_direct_outputs():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock()
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    outputs = (
        {
            "type": "symbolic",
            "outputData": {
                "name": "x",
                "value": "<mathml>x</mathml>",
                "latex": "x",
            },
        },
        {
            "type": "symbolic",
            "outputData": {
                "name": "y",
                "value": "<mathml>y</mathml>",
                "latex": "y",
            },
        },
    )

    results = [r async for r in processor.process(_as_async_iter(*outputs))]

    assert [result.to_content()["data"]["text/latex"] for result in results] == [
        "x =$\\\\\\ \\displaystyle{}x$",
        "y =$\\\\\\ \\displaystyle{}y$",
    ]
    mock_helper.convert_mathml_to_latex.assert_not_awaited()


@pytest.mark.asyncio
async def test_output_processor_symbolic_converted_latex_named():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value="x^2")
    mock_logger = MagicMock()
    processor = OutputProcessor(mwi_comm_helper=mock_helper, logger=mock_logger)

    out = {
        "type": "symbolic",
        "outputData": {"name": "y", "value": "<mathml>...</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    assert result.msg_type == "execute_result"
    content = result.to_content()
    assert content["data"]["text/latex"] == "y =$\\\\\\ \\displaystyle{}x^2$"
    mock_helper.convert_mathml_to_latex.assert_awaited_once_with("<mathml>...</mathml>")
    mock_logger.debug.assert_any_call(
        "Direct LaTeX unavailable; converting symbolic MathML to LaTeX"
    )


@pytest.mark.asyncio
async def test_output_processor_symbolic_converted_latex_unnamed():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value="x^2")
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "<mathml>...</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    content = result.to_content()
    assert content["data"]["text/latex"] == "$\\displaystyle{}x^2$"
    mock_helper.convert_mathml_to_latex.assert_awaited_once_with("<mathml>...</mathml>")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_latex", ["", None, 42])
async def test_output_processor_symbolic_invalid_direct_latex_uses_conversion(
    invalid_latex,
):
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value="x^2")
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {
            "name": "y",
            "value": "<mathml>...</mathml>",
            "latex": invalid_latex,
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, LatexResultOutput)
    assert (
        result.to_content()["data"]["text/latex"] == "y =$\\\\\\ \\displaystyle{}x^2$"
    )
    mock_helper.convert_mathml_to_latex.assert_awaited_once_with("<mathml>...</mathml>")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["f", ""])
async def test_output_processor_symbolic_direct_and_converted_format_identically(name):
    latex_body = "\n  x^2 + y^2  \n"
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value=latex_body)
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    direct_out = {
        "type": "symbolic",
        "outputData": {
            "name": name,
            "value": "<direct-mathml>",
            "latex": latex_body,
        },
    }
    converted_out = {
        "type": "symbolic",
        "outputData": {"name": name, "value": "<converted-mathml>"},
    }

    direct_result = [r async for r in processor.process(_as_async_iter(direct_out))][0]
    converted_result = [
        r async for r in processor.process(_as_async_iter(converted_out))
    ][0]

    assert (
        direct_result.to_content()["data"]["text/latex"]
        == converted_result.to_content()["data"]["text/latex"]
    )
    mock_helper.convert_mathml_to_latex.assert_awaited_once_with("<converted-mathml>")


@pytest.mark.asyncio
async def test_output_processor_symbolic_returns_none():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value=None)
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "<mathml>content</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert (
        content["data"]["text/html"]
        == "<html><pre><mathml>content</mathml></pre></html>"
    )
    assert content["data"]["text/plain"] == "<mathml>content</mathml>"


@pytest.mark.asyncio
async def test_output_processor_symbolic_returns_empty_string():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(return_value="")
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "<mathml>content</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert (
        content["data"]["text/html"]
        == "<html><pre><mathml>content</mathml></pre></html>"
    )
    assert content["data"]["text/plain"] == "<mathml>content</mathml>"


@pytest.mark.asyncio
async def test_output_processor_symbolic_conversion_failure():
    mock_helper = MagicMock()
    mock_helper.convert_mathml_to_latex = AsyncMock(
        side_effect=Exception("conversion failed")
    )
    processor = OutputProcessor(mwi_comm_helper=mock_helper)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "<mathml>content</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert (
        content["data"]["text/html"]
        == "<html><pre><mathml>content</mathml></pre></html>"
    )
    assert content["data"]["text/plain"] == "<mathml>content</mathml>"


@pytest.mark.asyncio
async def test_output_processor_symbolic_no_helper():
    processor = OutputProcessor(mwi_comm_helper=None)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "<mathml>content</mathml>"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert (
        content["data"]["text/html"]
        == "<html><pre><mathml>content</mathml></pre></html>"
    )
    assert content["data"]["text/plain"] == "<mathml>content</mathml>"


@pytest.mark.asyncio
async def test_output_processor_symbolic_empty_payload():
    processor = OutputProcessor(mwi_comm_helper=None)

    out = {
        "type": "symbolic",
        "outputData": {"name": "", "value": "", "latex": ""},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert content["data"]["text/html"] == "<html><pre></pre></html>"
    assert content["data"]["text/plain"] == ""


# ---- Figure Tests ----


@pytest.mark.asyncio
async def test_output_processor_figure():
    processor = OutputProcessor()

    out = {
        "type": "figure",
        "outputData": {
            "figureId": "figure_1",
            "figureImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "figureSize": [560, 420],
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, FigureOutput)
    assert result.msg_type == "update_display_data"
    content = result.to_content()
    assert "image/png" in content["data"]
    assert content["data"]["image/png"] == "iVBORw0KGgoAAAANSUhEUgAA..."
    assert content["metadata"]["image/png"] == {"width": 560, "height": 420}
    assert content["transient"]["display_id"] == "figure_1"


@pytest.mark.asyncio
async def test_output_processor_figure_placeholder():
    processor = OutputProcessor()

    out = {
        "type": "figure",
        "outputData": {"figurePlaceHolderId": "fig_1"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, FigurePlaceholderOutput)
    assert result.msg_type == "display_data"
    content = result.to_content()
    assert content["data"] == {}
    assert content["metadata"] == {}
    assert content["transient"]["display_id"] == "fig_1"


@pytest.mark.asyncio
async def test_output_processor_figure_malformed():
    processor = OutputProcessor()

    out = {
        "type": "figure",
        "outputData": {
            "figureId": "f1",
            "figureImage": "not-a-data-uri",
            "figureSize": [560, 420],
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    # Malformed figure data returns None
    assert result is None


@pytest.mark.asyncio
async def test_output_processor_figure_non_image_mimetype():
    processor = OutputProcessor()

    out = {
        "type": "figure",
        "outputData": {
            "figureId": "f1",
            "figureImage": "data:text/plain;base64,SGVsbG8=",
            "figureSize": [560, 420],
        },
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    # Non-image mimetype should be rejected
    assert result is None


# ---- HTML Tests ----


@pytest.mark.asyncio
async def test_output_processor_html():
    processor = OutputProcessor()

    out = {
        "type": "text/html",
        "outputData": "<i>italic</i>",
    }

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert isinstance(result, HtmlResultOutput)
    content = result.to_content()
    assert content["data"]["text/html"] == "<i>italic</i>"
    assert content["data"]["text/plain"] == "<i>italic</i>"


# ---- Markdown Tests ----


@pytest.mark.asyncio
async def test_output_processor_markdown():
    processor = OutputProcessor()

    out = {
        "type": "markdown",
        "outputData": {"content": "**bold text**"},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, MarkdownResultOutput)
    assert result.msg_type == "execute_result"
    assert result.to_content() == {
        "data": {"text/markdown": "**bold text**"},
        "metadata": {},
    }


@pytest.mark.asyncio
async def test_output_processor_markdown_preserves_source():
    processor = OutputProcessor()
    markdown = (
        "  # Heading\n\n"
        "| 언어 | 값 |\n"
        "| --- | --- |\n"
        "| MATLAB | $x^2$ |\n\n"
        "```matlab\n"
        "x = 1;\n"
        "```\n"
    )

    out = {
        "type": "markdown",
        "outputData": {"content": markdown},
    }

    results = [r async for r in processor.process(_as_async_iter(out))]

    assert len(results) == 1
    result = results[0]
    assert result.markdown == markdown
    assert result.to_content()["data"] == {"text/markdown": markdown}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("output_data", "expected"),
    [
        ({"content": "   "}, "   "),
        ({"content": "\n"}, "\n"),
        ({}, ""),
    ],
)
async def test_output_processor_markdown_edge_cases(output_data, expected):
    processor = OutputProcessor()

    out = {
        "type": "markdown",
        "outputData": output_data,
    }

    results = [r async for r in processor.process(_as_async_iter(out))]

    assert len(results) == 1
    assert results[0].to_content()["data"] == {"text/markdown": expected}


# ---- Edge Cases ----


@pytest.mark.asyncio
async def test_output_processor_unknown_type():
    processor = OutputProcessor()

    out = {"type": "unknown_type", "outputData": {"text": "something"}}

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert result is None


@pytest.mark.asyncio
async def test_output_processor_missing_type_key():
    processor = OutputProcessor()

    out = {"outputData": {"text": "orphan"}}

    results = [r async for r in processor.process(_as_async_iter(out))]
    result = results[0] if results else None

    assert result is None
