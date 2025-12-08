# Copyright 2025 The MathWorks, Inc.

from datetime import datetime
import errno
import sys
import tempfile
from unittest.mock import patch

import jupyter_client.kernelspec
import pytest

from jupyter_matlab_kernel.kernelspec import (
    STANDARD_PYTHON_EXECUTABLE,
    get_kernel_spec,
    main,
)


def test_get_kernel_spec_default_executable():
    """
    Test that get_kernel_spec() returns the default Python executable.
    """
    kernelspec = get_kernel_spec()
    assert kernelspec["argv"][0] == STANDARD_PYTHON_EXECUTABLE


def test_get_kernel_spec_custom_executable():
    """
    Test that get_kernel_spec() uses a custom executable when provided.
    """
    custom_executable = "/usr/bin/python3.10"
    kernelspec = get_kernel_spec(executable=custom_executable)
    assert kernelspec["argv"][0] == custom_executable


def test_get_kernel_spec_structure():
    """
    Test that get_kernel_spec() returns a dictionary with the expected keys.
    """
    kernelspec = get_kernel_spec()
    assert "argv" in kernelspec
    assert "display_name" in kernelspec
    assert "language" in kernelspec
    assert "interrupt_mode" in kernelspec
    assert "env" in kernelspec
    assert "metadata" in kernelspec


def test_get_kernel_spec_metadata():
    """
    Test that get_kernel_spec() returns a dictionary with the expected metadata keys.
    """
    kernelspec = get_kernel_spec()
    assert "debugger" in kernelspec["metadata"]
    assert "copyright" in kernelspec["metadata"]
    assert "description" in kernelspec["metadata"]


def test_get_kernel_spec_copyright_year():
    """
    Test that get_kernel_spec() returns a copyright year range that includes the current year.
    """
    kernelspec = get_kernel_spec()
    current_year = datetime.now().year
    assert f"Copyright 2023-{current_year}" in kernelspec["metadata"]["copyright"]


def test_get_kernel_spec_argv_structure():
    """
    Test that get_kernel_spec() returns the expected argv structure.
    """
    kernelspec = get_kernel_spec()
    assert len(kernelspec["argv"]) == 5
    assert kernelspec["argv"][1] == "-m"
    assert kernelspec["argv"][2] == "jupyter_matlab_kernel"
    assert kernelspec["argv"][3] == "-f"
    assert kernelspec["argv"][4] == "{connection_file}"


def test_get_kernel_spec_display_name():
    """
    Test that get_kernel_spec() returns the correct display name.
    """
    kernelspec = get_kernel_spec()
    assert kernelspec["display_name"] == "MATLAB Kernel"


def test_get_kernel_spec_language():
    """
    Test that get_kernel_spec() returns the correct language.
    """
    kernelspec = get_kernel_spec()
    assert kernelspec["language"] == "matlab"


def test_get_kernel_spec_interrupt_mode():
    """
    Test that get_kernel_spec() returns the correct interrupt mode.
    """
    kernelspec = get_kernel_spec()
    assert kernelspec["interrupt_mode"] == "message"


def test_get_kernel_spec_env():
    """
    Test that get_kernel_spec() returns an empty dictionary for the env key.
    """
    kernelspec = get_kernel_spec()
    assert isinstance(kernelspec["env"], dict)
    assert len(kernelspec["env"]) == 0


def test_main_install_kernelspec(capsys, tmp_path, monkeypatch):
    """
    Test the main function for installing the MATLAB kernel spec.

    This test mocks system arguments, Python executable path, and kernel installation.
    It verifies that the correct output is printed after installing the kernel spec.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec"])
    monkeypatch.setattr(sys, "executable", "/path/to/python")
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))
    monkeypatch.setattr(
        jupyter_client.kernelspec,
        "install_kernel_spec",
        lambda *args, **kwargs: "/fake/path",
    )

    with patch("jupyter_matlab_kernel.kernelspec.install_kernel_spec") as mock_install:
        mock_install.return_value = ("/fake/path", {"key": "value"})
        main()

    captured = capsys.readouterr()
    assert (
        "Installed the following kernelspec for jupyter_matlab_kernel in /fake/path"
        in captured.out
    )
    assert '"key": "value"' in captured.out


def test_main_reset(capsys, tmp_path, monkeypatch):
    """
    Test the main function with the --reset flag.

    This test mocks system arguments and kernel installation.
    It verifies that the correct output is printed after resetting the kernel.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec", "--reset"])
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))
    monkeypatch.setattr(
        jupyter_client.kernelspec,
        "install_kernel_spec",
        lambda *args, **kwargs: "/fake/path",
    )

    with patch("jupyter_matlab_kernel.kernelspec.install_kernel_spec") as mock_install:
        mock_install.return_value = ("/fake/path", {"key": "value"})
        main()

    captured = capsys.readouterr()
    assert (
        "Installed the following kernelspec for jupyter_matlab_kernel in /fake/path"
        in captured.out
    )
    assert '"key": "value"' in captured.out


def test_main_permission_error(capsys, tmp_path, monkeypatch):
    """
    Test the main function when a permission error occurs during kernel installation.

    This test simulates a permission error when installing the kernel spec and
    verifies that the program exits with a SystemExit exception.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec"])
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))

    def raise_permission_error(*args, **kwargs):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(
        jupyter_client.kernelspec, "install_kernel_spec", raise_permission_error
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Permission denied" in captured.err


def test_main_other_oserror(capsys, tmp_path, monkeypatch):
    """
    Test the main function when a non-permission OSError occurs during kernel installation.

    This test simulates a "No such file or directory" error when installing the kernel spec
    and verifies that the program raises an OSError with the correct error number and message.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec"])
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))

    def raise_other_oserror(*args, **kwargs):
        raise OSError(errno.ENOENT, "No such file or directory")

    monkeypatch.setattr(
        jupyter_client.kernelspec, "install_kernel_spec", raise_other_oserror
    )

    with pytest.raises(OSError) as excinfo:
        main()

    assert excinfo.value.errno == errno.ENOENT
    assert "No such file or directory" in str(excinfo.value)


def test_main_preview(capsys, tmp_path, monkeypatch):
    """
    Test the main function with dry run option.

    This test verifies that the program exits successfully and prints the expected
    output when the --preview option is used.
    """
    custom_executable = "/path/to/python"
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec", "--preview"])
    monkeypatch.setattr(sys, "executable", custom_executable)
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))
    monkeypatch.setattr(sys, "prefix", "/fake/prefix")

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert (
        "The following kernelspec for jupyter_matlab_kernel would be installed in"
        in captured.out
    )
    assert f"{custom_executable}" in captured.out


def test_main_reset_with_preview(capsys, tmp_path, monkeypatch):
    """
    Test the main function with reset and dry run options.

    This test checks that the program exits successfully and prints the expected
    output when both --reset and --preview options are used.
    """
    monkeypatch.setattr(
        sys, "argv", ["install-matlab-kernelspec", "--reset", "--preview"]
    )
    monkeypatch.setattr(tempfile, "mkdtemp", lambda: str(tmp_path))
    monkeypatch.setattr(sys, "prefix", "/fake/prefix")

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert (
        "The following kernelspec for jupyter_matlab_kernel would be installed in"
        in captured.out
    )
    assert f"{STANDARD_PYTHON_EXECUTABLE}" in captured.out


def test_main_argparse_help(capsys, monkeypatch):
    """
    Test the main function's help output.

    This test ensures that the program exits successfully and displays the
    correct help information when the --help option is used.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec", "--help"])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "usage: install-matlab-kernelspec" in captured.out
    assert "--reset" in captured.out
    assert "--preview" in captured.out


def test_main_unknown_argument(capsys, monkeypatch):
    """
    Test the main function with an unknown argument.

    This test verifies that the program exits with an error code and
    displays an appropriate error message when an unknown argument is provided.
    """
    monkeypatch.setattr(sys, "argv", ["install-matlab-kernelspec", "--unknown"])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "error: unrecognized arguments: --unknown" in captured.err
