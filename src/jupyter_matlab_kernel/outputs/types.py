# Copyright 2026 The MathWorks, Inc.

"""Frozen dataclasses for Jupyter iopub output messages.

Hierarchy mirrors the Jupyter messaging protocol:
  JupyterOutput (abstract base)
  ├── StreamOutput (abstract)
  │   ├── StdoutOutput
  │   └── StderrOutput
  ├── ClearOutput
  └── DataBundleOutput (abstract, data*, metadata*)
      ├── ExecuteResultOutput
      │   ├── HtmlResultOutput
      │   ├── LatexResultOutput
      │   └── MarkdownResultOutput
      └── DisplayDataOutput (display_id: str | None)
          ├── FigurePlaceholderOutput
          └── UpdateDisplayDataOutput (display_id required)
              └── FigureOutput
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JupyterOutput(ABC):
    """Base class for all Jupyter iopub output messages."""

    @property
    @abstractmethod
    def msg_type(self) -> str: ...

    @abstractmethod
    def to_content(self) -> dict: ...


@dataclass(frozen=True, slots=True)
class StreamOutput(JupyterOutput):
    """Base class for stdout/stderr stream messages."""

    text: str

    @property
    def msg_type(self) -> str:
        return "stream"

    @property
    @abstractmethod
    def name(self) -> str: ...

    def to_content(self) -> dict:
        return {"name": self.name, "text": self.text}


@dataclass(frozen=True, slots=True)
class StdoutOutput(StreamOutput):
    """A stdout stream message."""

    @property
    def name(self) -> str:
        return "stdout"


@dataclass(frozen=True, slots=True)
class StderrOutput(StreamOutput):
    """A stderr stream message."""

    @property
    def name(self) -> str:
        return "stderr"


@dataclass(frozen=True, slots=True)
class ClearOutput(JupyterOutput):
    """A clear_output message."""

    wait: bool = False

    @property
    def msg_type(self) -> str:
        return "clear_output"

    def to_content(self) -> dict:
        return {"wait": self.wait}


@dataclass(frozen=True, slots=True)
class DataBundleOutput(JupyterOutput):
    """Base for messages carrying a data/metadata bundle.

    Subclasses implement msg_type, data, and metadata.
    """

    @property
    @abstractmethod
    def data(self) -> dict: ...

    @property
    @abstractmethod
    def metadata(self) -> dict: ...

    def to_content(self) -> dict:
        return {"data": self.data, "metadata": self.metadata}


@dataclass(frozen=True, slots=True)
class ExecuteResultOutput(DataBundleOutput):
    """Base class for execute_result messages."""

    @property
    def msg_type(self) -> str:
        return "execute_result"


@dataclass(frozen=True, slots=True)
class HtmlResultOutput(ExecuteResultOutput):
    """An execute_result containing text/html data."""

    html: str
    text: str

    @property
    def data(self) -> dict:
        return {"text/html": self.html, "text/plain": self.text}

    @property
    def metadata(self) -> dict:
        return {}


@dataclass(frozen=True, slots=True)
class LatexResultOutput(ExecuteResultOutput):
    """An execute_result containing text/latex data."""

    latex: str

    @property
    def data(self) -> dict:
        return {"text/latex": self.latex}

    @property
    def metadata(self) -> dict:
        return {}


@dataclass(frozen=True, slots=True)
class MarkdownResultOutput(ExecuteResultOutput):
    """An execute_result containing text/markdown data."""

    markdown: str

    @property
    def data(self) -> dict:
        return {"text/markdown": self.markdown}

    @property
    def metadata(self) -> dict:
        return {}


@dataclass(frozen=True, slots=True)
class DisplayDataOutput(DataBundleOutput):
    """Base class for display_data messages. Supports optional display_id."""

    display_id: str | None = field(default=None, kw_only=True)

    @property
    def msg_type(self) -> str:
        return "display_data"

    def to_content(self) -> dict:
        # Explicit two-arg super() needed: zero-arg super() breaks with
        # slots=True in deep frozen-dataclass hierarchies. For more info
        # https://stackoverflow.com/questions/79446265/python-dataclassesslots-true-breaks-super
        content = super(DisplayDataOutput, self).to_content()
        if self.display_id is not None:
            content["transient"] = {"display_id": self.display_id}
        return content


@dataclass(frozen=True, slots=True)
class FigurePlaceholderOutput(DisplayDataOutput):
    """A display_data reserving a display slot for a figure via display_id."""

    @property
    def data(self) -> dict:
        return {}

    @property
    def metadata(self) -> dict:
        return {}


@dataclass(frozen=True, slots=True)
class UpdateDisplayDataOutput(DisplayDataOutput):
    """Base class for update_display_data messages. display_id is required."""

    def __post_init__(self):
        if not self.display_id:
            raise ValueError("display_id is required for update_display_data messages")

    @property
    def msg_type(self) -> str:
        return "update_display_data"


@dataclass(frozen=True, slots=True)
class FigureOutput(UpdateDisplayDataOutput):
    """An update_display_data message containing a figure image."""

    mimetype: str
    image_data: str
    width: int
    height: int

    @property
    def data(self) -> dict:
        return {self.mimetype: self.image_data}

    @property
    def metadata(self) -> dict:
        return {self.mimetype: {"width": self.width, "height": self.height}}
