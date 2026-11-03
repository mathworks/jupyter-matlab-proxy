# Copyright 2026 The MathWorks, Inc.

import inspect
import re
from collections.abc import AsyncGenerator

from jupyter_matlab_kernel import mwi_logger
from jupyter_matlab_kernel.outputs.types import (
    FigureOutput,
    FigurePlaceholderOutput,
    HtmlResultOutput,
    JupyterOutput,
    LatexResultOutput,
    StderrOutput,
    StdoutOutput,
)

_logger = mwi_logger.get()


class OutputProcessor:
    """Processes raw MATLAB outputs and converts them into Jupyter-compatible
    output dataclasses.
    """

    def __init__(self, mwi_comm_helper=None, logger=None):
        self.mwi_comm_helper = mwi_comm_helper
        self.log = logger or _logger
        self.figure_ids = set()
        self._handler_registry = {
            "matrix": self._handle_matrix,
            "variable": self._handle_variable,
            "variableString": self._handle_variable_string,
            "symbolic": self._handle_symbolic,
            "figure": self._handle_figure,
            "text/html": self._handle_html,
            "error": self._handle_stderr,
            "warning": self._handle_stderr,
            "stderr": self._handle_stderr,
            "text": self._handle_stdout,
        }

    async def process(self, raw_outputs) -> AsyncGenerator[JupyterOutput, None]:
        """Process a stream of raw outputs, yielding JupyterOutput objects."""
        # Clear figure ids before each processing
        self.figure_ids.clear()

        async for out in raw_outputs:
            self.log.debug(f"Received output from MATLAB:\n{out}")
            if "type" not in out:
                continue

            out_type = out["type"]
            handler = self._handler_registry.get(out_type)
            if handler:
                result = handler(out.get("outputData", {}))
                if inspect.isawaitable(result):
                    result = await result
                if result is not None:
                    yield result
            else:
                self.log.warning(f"Unknown output type '{out_type}', skipping")

    def _wrap_as_preformatted_html(self, text: str) -> str:
        """Wrap text in <html><pre> tags for display."""
        return f"<html><pre>{text}</pre></html>"

    def _handle_matrix(self, output) -> HtmlResultOutput:
        name = output.get("name", "")
        header = output.get("header", "")
        otype = output.get("type", "")
        value = output.get("value", "")

        text = f"{name} = {header} {otype}\n{value}"
        if output.get("rows", 0) > 10 or output.get("columns", 0) > 30:
            text += "..."

        return HtmlResultOutput(html=self._wrap_as_preformatted_html(text), text=text)

    def _handle_variable(self, output) -> HtmlResultOutput:
        name = output.get("name", "")
        header = output.get("header", "")
        value = output.get("value", "")

        indentation = "" if not header else "\n    "
        text = f"{name} = {header}{indentation}{value}"
        return HtmlResultOutput(html=self._wrap_as_preformatted_html(text), text=text)

    def _handle_variable_string(self, output) -> HtmlResultOutput:
        name = output.get("name", "")
        header = output.get("header", "")
        value = output.get("value", "")

        use_single_line_display = "\n" not in value
        indentation = ""
        if not use_single_line_display or header:
            indentation = "\n"

        text = f"{name} = {header}{indentation}{value}"
        return HtmlResultOutput(html=self._wrap_as_preformatted_html(text), text=text)

    async def _handle_symbolic(self, output) -> JupyterOutput:
        name = output.get("name", "")
        direct_latex = output.get("latex")

        if isinstance(direct_latex, str) and direct_latex:
            self.log.debug(
                "Using direct LaTeX from symbolic output received from MATLAB"
            )
            return self._create_symbolic_latex_output(name, direct_latex)

        mathml = output.get("value", "")
        if self.mwi_comm_helper:
            self.log.debug(
                "Direct LaTeX unavailable; converting symbolic MathML to LaTeX"
            )
            try:
                converted_latex = await self.mwi_comm_helper.convert_mathml_to_latex(
                    mathml
                )
                if converted_latex:
                    return self._create_symbolic_latex_output(name, converted_latex)
            except Exception as error:
                self.log.warning(f"Failed to convert MathML to LaTeX: {error}")

        return HtmlResultOutput(
            html=self._wrap_as_preformatted_html(mathml), text=mathml
        )

    def _create_symbolic_latex_output(
        self, name: str, latex_body: str
    ) -> LatexResultOutput:
        if name:
            latex = f"{name} =$\\\\\\ \\displaystyle{{}}{latex_body}$"
        else:
            latex = f"$\\displaystyle{{}}{latex_body}$"
        return LatexResultOutput(latex=latex)

    def _handle_figure(self, output_data) -> JupyterOutput | None:
        if "figurePlaceHolderId" in output_data:
            # MATLAB may send multiple placeholder outputs with the same figureId.
            # We only need the first placeholder output to preserve the order and
            # can discard the remaining placeholder outputs.
            figure_id = output_data["figurePlaceHolderId"]
            if figure_id not in self.figure_ids:
                self.figure_ids.add(figure_id)
                return FigurePlaceholderOutput(display_id=figure_id)
        elif "figureImage" in output_data:
            fid = output_data.get("figureId", "")
            return self._parse_figure_image(
                fid, output_data["figureImage"], output_data.get("figureSize", [])
            )
        return None

    def _parse_figure_image(
        self, display_id: str, base64_data: str, figure_size: list
    ) -> FigureOutput | None:
        """Parse a base64 data URI and return a FigureOutput, or None if malformed."""
        # Format is "data:image/png;base64,<base64_value>"
        match = re.match(r"data:(?P<mimetype>.*);base64,(?P<value>.*)", base64_data)
        if match:
            mimetype = match.group("mimetype")
            if not mimetype.startswith("image/"):
                self.log.warning(f"Unexpected figure mimetype: {mimetype}")
                return None
            width = int(figure_size[0])
            height = int(figure_size[1])
            return FigureOutput(
                mimetype=mimetype,
                image_data=match.group("value"),
                width=width,
                height=height,
                display_id=display_id,
            )
        self.log.warning(f"Malformed figure data: {base64_data[:100]}...")
        return None

    def _handle_stdout(self, output_data) -> StdoutOutput:
        return StdoutOutput(text=output_data.get("text", ""))

    def _handle_stderr(self, output_data) -> StderrOutput:
        return StderrOutput(text=output_data.get("text", ""))

    def _handle_html(self, output_data) -> HtmlResultOutput:
        """Process text/html output data."""
        return HtmlResultOutput(html=str(output_data), text=str(output_data))
