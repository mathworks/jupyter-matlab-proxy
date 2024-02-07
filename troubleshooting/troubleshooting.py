# Copyright 2023-2024 The MathWorks, Inc.
# Script to help users troubleshoot common errors with the environment
# This script is designed to be used in standalone manner and to maintain
# that, it doesn't use utility functions present in the parent repository.

import os
import platform
import shutil
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Final

GREEN_OK: Final = "\033[32mOK\033[0m" if os.name != "nt" else "ok"
RED_X: Final = "\033[31m X\033[0m" if os.name != "nt" else " X"
OS_TYPE: Final = platform.system()


def list_matlab():
    title, key = "MATLAB", "matlab"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [FindExecutableHandler(key)]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def list_matlab_proxy_on_path():
    title, key = "matlab-proxy-app", "matlab-proxy-app"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [FindExecutableHandler(key)]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def list_jupyter_executable():
    title, key = "Jupyter", "jupyter"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [FindExecutableHandler(key)]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def check_python_and_pip_installed():
    title, key = (
        "Python and pip executables",
        "python/pip",
    )
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [
        CommandVersionHandler("python"),
        CommandVersionHandler("pip"),
        CommandVersionHandler("python3"),
    ]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def os_info():
    title = "OS information"
    header = generate_header(title)
    os_data = [
        platform.system(),
        platform.release(),
        platform.platform(),
        platform.uname(),
        "\n",
    ]
    return header + "\n".join(f"{cmd}" for cmd in os_data)


def list_installed_packages():
    title = "Installed packages"
    key = "packages"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [CommandProviderHandler(key, OS_TYPE)]
    env_info = EnvInfo(os_filter, TitleHandler(title), handlers)
    return env_info.print()


def list_xvfb() -> str:
    title, key = "Xvfb", "Xvfb"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [FindExecutableHandler(key)]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def list_conda_related_information() -> str:
    title, key = "Conda information", "conda"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [CommandVersionHandler(key)]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def list_server_extensions():
    title, key = (
        "Jupyter server extensions",
        "extensions",
    )
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [
        CommandOutputHandler(key, "jupyter server extension list"),
        CommandOutputHandler(key, "jupyter labextension list"),
    ]
    status = EnvInfo(os_filter, TitleHandler(title), handlers)
    return status.print()


def list_env_vars() -> str:
    title = "Environment variables"
    key = "Env"
    os_filter = OSFilter(OS_TYPE, key)
    handlers = [CommandProviderHandler(key, OS_TYPE)]
    env_info = EnvInfo(os_filter, TitleHandler(title), handlers)
    return env_info.print()


class EnvInfo:
    """Base class that contains filter to determine execution
    and handlers for specific tasks"""

    def __init__(self, filter, title_handler, handlers: list) -> None:
        self.filter = filter
        self.title_handler = title_handler
        self.handlers = handlers

    def print(self):
        if self.filter.filter():
            title = self.title_handler.execute()
            output = "\n".join(h.execute() for h in self.handlers if h.execute())
            return "\n".join([title, output]) if output else ""
        else:
            return ""


# Filters
class OSFilter:
    """Helps filter out commands on the basis of platform"""

    def __init__(self, os_type: str, key: str) -> None:
        self.os_type = os_type
        self.key = key
        self.data = {
            "Xvfb": {"Linux": True, "Windows": False, "Darwin": False},
            "Env": {"Linux": True, "Windows": True, "Darwin": True},
            "conda": {"Linux": True, "Windows": True, "Darwin": True},
            "matlab": {"Linux": True, "Windows": True, "Darwin": True},
            "matlab-proxy-app": {"Linux": True, "Windows": True, "Darwin": True},
            "jupyter": {"Linux": True, "Windows": True, "Darwin": True},
            "python/pip": {"Linux": True, "Windows": True, "Darwin": True},
            "os": {"Linux": True, "Windows": True, "Darwin": True},
            "packages": {"Linux": True, "Windows": True, "Darwin": True},
            "extensions": {"Linux": True, "Windows": True, "Darwin": True},
        }

    def filter(self):
        return self.data[self.key][self.os_type]


class OptionalFilter:
    """Provides error icons and recommendation based on optionality"""

    def __init__(self, key: str) -> None:
        self.key: str = key
        self.data = {
            "Xvfb": False,
            "Env": True,
            "conda": True,
            "matlab": False,
            "matlab-proxy-app": False,
            "jupyter": False,
            "python": False,
            "pip": False,
            "python3": False,
            "packages": True,
            "extensions": True,
        }

    def filter(self) -> bool:
        return self.data[self.key]


class CommandProvider:
    """Provides OS-specific command alternatives"""

    def __init__(self, os_type: str, key: str) -> None:
        self.os_type = os_type
        self.key = key
        self.data = {
            "Env": {
                "Linux": 'env | grep -iE "^[^=]*matlab|^[^=]*mw_|^[^=]*mwi_"',
                "Windows": 'set | findstr /IR "^[^=]*matlab ^[^=]*mw_ ^[^=]*mwi_"',
                "Darwin": 'env | grep -iE "^[^=]*matlab|^[^=]*mw_|^[^=]*mwi_"',
            },
            "packages": {
                "Linux": 'python -m pip list | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy|notebook"',
                "Windows": 'python -m pip list | findstr /IR "jupyter matlab-proxy jupyter-matlab-proxy notebook"',
                "Darwin": 'python -m pip list | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy|notebook"',
            },
        }

    def get_command(self):
        result = self.data.get(self.key)
        return result if result is None else result[self.os_type]


# handlers
class TitleHandler:
    """Returns the title for the command block"""

    def __init__(self, title: str) -> None:
        self.title = title

    def execute(self):
        return generate_header(self.title)


class CommandProviderHandler:
    """Handler to apply the command provider pattern to the desired commands"""

    def __init__(self, key: str, os_type: str) -> None:
        self.key = key
        self.os_type = os_type

    def execute(self):
        is_suggestion_optional = OptionalFilter(self.key).filter()

        # Get the command from the command provider
        cmd_provider = CommandProvider(self.os_type, self.key)
        cmd = cmd_provider.get_command()
        rep: Report = process_output(exec_command, is_suggestion_optional, cmd)
        return str(rep)


class CommandVersionHandler:
    """Handler to apply the command version pattern to the desired commands"""

    def __init__(self, key: str) -> None:
        self.key = key

    def execute(self) -> str:
        is_suggestion_optional = OptionalFilter(self.key).filter()
        outputs = find_executable_and_version(self.key, is_suggestion_optional)
        return "".join(str(op) for op in outputs)


class CommandOutputHandler:
    """Handler to apply the command output pattern to the desired commands"""

    def __init__(self, key: str, cmd: str) -> None:
        self.key = key
        self.cmd = cmd

    def execute(self):
        is_suggestion_optional = OptionalFilter(self.key).filter()
        rep: Report = process_output(exec_command, is_suggestion_optional, self.cmd)
        return str(rep)


class FindExecutableHandler:
    """Handler to apply the find executable pattern to the desired commands"""

    def __init__(self, key: str) -> None:
        self.key = key

    def execute(self):
        is_suggestion_optional = OptionalFilter(self.key).filter()
        rep = process_output(find_executable, is_suggestion_optional, self.key)
        return str(rep)


@dataclass
class cmd_output:
    """A class to store the output generated by running system commands
    Returns:
        object: returns an object with overridden magic str method
    """

    command: str
    output: str
    isError: bool

    def __str__(self) -> str:
        return f"{self.command} - {self.output} "


@dataclass
class cmd_only_output(cmd_output):
    """Subclass to cmd_output which overrides the magic str method differently"""

    def __str__(self) -> str:
        return f"{self.output} "


@dataclass
class Report:
    body: str
    recommendations: str
    has_error: bool
    err_icon: str

    def __str__(self) -> str:
        return "".join([self.body, self.err_icon, "\n", self.recommendations])


def find_executable(*args) -> list:
    """Runs which command (or OS type equivalent of which) to find the executable on path

    Returns:
        output: A list of outputs of the executed commands
    """
    output: list = []
    for name in args:
        executable_path = shutil.which(name)
        real_path = real_executable_path = None
        # Using readlink to find the actual path of the executable, if one exists
        with suppress(OSError):
            if executable_path is not None:
                real_path = os.readlink(Path(executable_path).parent.absolute())
                real_executable_path = Path(real_path, name)
        output.append(
            cmd_output(
                name,
                (
                    real_executable_path
                    if real_executable_path is not None
                    else executable_path
                ),
                True if executable_path is None else False,
            )
        )
    return output


def process_output(func, is_suggestion_optional, *args) -> Report:
    """Higher-order helper function that calls find_executable/exec_command and primes the output for reporting

    Args:
        func (*args): Expects either of find_executable or exec_command functions as input
        suppress_suggestions (bool): option to suppress suggestions shown to the user

    Returns:
        Report: An object of dataclass Report that contains information like command output,
        errors, recommendations to be made to the users.
    """

    body: str = ""
    error: bool = False
    err_recommendation: str = ""
    err_icon = ""
    for cmd_pair in func(*args):
        body = str(cmd_pair)
        if cmd_pair.output is None:
            error = True
        # Branch where we want to display suggestions and validation status
        if not is_suggestion_optional:
            if error:
                err_recommendation = f"Recommendation: {cmd_pair.command} is not installed. Please install {cmd_pair.command}.\n"
                err_icon = RED_X
            else:
                err_icon = GREEN_OK
    rep = Report(
        body=body,
        recommendations=err_recommendation,
        has_error=error,
        err_icon=err_icon,
    )
    return rep


def generate_header(title: str) -> str:
    """Generates a prettified header block for all individual pieces of information

    Args:
        title (str): main headline of the block

    Returns:
        str: prettified string
    """
    return (
        str(
            prettify(
                boundary_filler="-",
                text_arr=[f"{title}"],
            )
        )
        + "\n"
    )


def prettify(boundary_filler=" ", text_arr=[]) -> str:
    """Prettify array of strings with borders for stdout

        Args:
        boundary_filler (str, optional): Upper and lower border filler for text. Defaults to " ".
        text_arr (list, optional):The text array to prettify. Each element will be added to a newline. Defaults to [].

    Returns:
        [str]: Prettified String
    """

    import sys

    if not sys.stdout.isatty():
        return (
            "\n============================\n"
            + "\n".join(text_arr)
            + "\n============================\n"
        )

    size = os.get_terminal_size()
    cols, _ = size.columns, size.lines
    if any(len(text) > cols for text in text_arr):
        result = ""
        for text in text_arr:
            result += text + "\n"
        return result
    upper = "\n" + "".ljust(cols, boundary_filler) + "\n" if len(text_arr) > 0 else ""
    lower = "".ljust(cols, boundary_filler) if len(text_arr) > 0 else ""

    content = ""
    for text in text_arr:
        content += text.center(cols) + "\n"
    result = upper + content + lower
    return result


def exec_command(*args) -> list:
    """A utility to run a custom command and gather output.

    Returns:
        list: of outputs that are returned by the function
    """
    output: list = []
    for cmd in args:
        try:
            completed_process = subprocess.run(
                cmd, shell=True, capture_output=True, timeout=10, text=True
            )
            output.append(
                cmd_only_output(
                    cmd,
                    completed_process.stdout.strip() + completed_process.stderr.strip(),
                    False if completed_process.stderr == "" else True,
                )
            )
        except TimeoutError:
            output.append(cmd_only_output(cmd, f"{cmd} command timed out!", True))
    return output


def find_executable_and_version(cmd: str, is_suggestions_optional: bool) -> list:
    """A helper function to execute which command along with --version option

    Args:
        cmd (str): command to be executed
        is_suggestions_optional (bool): provides an option to suppress suggestions that are
        displayed to the user.

    Returns:
        list: containing which command output and the version information output
    """
    output: list = []
    version = ""
    rep = process_output(find_executable, is_suggestions_optional, cmd)
    output.append(rep)

    if not rep.has_error:
        # Suppressing suggestions/error icon for version command
        version = process_output(exec_command, True, f"{cmd} --version")
        output.append("\n" + str(version))
    return output


output: str = ""
output += list_matlab()
output += list_matlab_proxy_on_path()
output += list_jupyter_executable()
output += check_python_and_pip_installed()
output += list_xvfb()
output += os_info()
output += list_conda_related_information()
output += list_installed_packages()
output += list_server_extensions()
output += list_env_vars()
print(output)
