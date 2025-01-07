# Copyright 2025 The MathWorks, Inc.

import argparse
import errno
import json
import pathlib
import shutil
import sys
import tempfile
from datetime import datetime

from jupyter_client import kernelspec

STANDARD_PYTHON_EXECUTABLE = "python3"


def get_kernel_spec(executable=None) -> dict:
    """
    Generate and return the kernelspec JSON for the MATLAB Kernel.

    This function creates a dictionary containing the necessary configuration
    for the MATLAB Kernel to be used with Jupyter. The kernelspec includes
    information such as the command to start the kernel, display name,
    language, and other metadata.

    For more information about kernelspecs, see:
    https://jupyter-client.readthedocs.io/en/latest/kernels.html#kernelspecs

    Args:
        executable (str, optional): The Python executable to use. Defaults to python3.

    Returns:
        dict: A dictionary containing the kernelspec configuration for the MATLAB Kernel.
    """
    if not executable:
        executable = STANDARD_PYTHON_EXECUTABLE

    copyright_start_year = 2023
    copyright_end_year = datetime.now().year

    kernelspec_json = {
        "argv": [
            executable,
            "-m",
            "jupyter_matlab_kernel",
            "-f",
            "{connection_file}",
        ],
        "display_name": "MATLAB Kernel",
        "language": "matlab",
        "interrupt_mode": "message",
        "env": {},
        "metadata": {
            "debugger": False,
            "copyright": f"Copyright {copyright_start_year}-{copyright_end_year} The MathWorks, Inc.",
            "description": "Jupyter kernelspec for MATLAB Kernel. For more information, please look at https://jupyter-client.readthedocs.io/en/stable/kernels.html#kernel-specs",
        },
    }
    return kernelspec_json


def install_kernel_spec(
    kernel_name: str, executable: str, kernelspec_dir, register_with_jupyter=True
):
    """
    Install the MATLAB Kernel kernelspec to the specified directory.

    Args:
        kernel_name (str): The name of the kernel to be installed.
        executable (str): The Python executable path to use for the kernelspec.
        kernelspec_dir (Path | str): The directory to install the kernelspec.
        register_with_jupyter (bool): Whether to register the kernelspec with Jupyter. Defaults to True. If True,
                                      the kernelspec will be installed to <prefix>/share/jupyter/kernels/<kernel_name>.

    Returns:
        tuple: A tuple containing the destination path of the installed kernelspec and the kernelspec dictionary.
    """
    kernelspec_dict = get_kernel_spec(executable)
    kernel_json_path = pathlib.Path(kernelspec_dir) / "kernel.json"

    # Copy kernelspec resources to the target directory
    shutil.copytree(pathlib.Path(__file__).parent / "kernelspec", kernelspec_dir)

    # Write the kernelspec to the kernel.json file
    with kernel_json_path.open("w") as f:
        json.dump(kernelspec_dict, f, indent=4)

    if register_with_jupyter:
        dest = kernelspec.install_kernel_spec(
            str(kernelspec_dir), kernel_name, prefix=sys.prefix
        )
    else:
        dest = str(kernelspec_dir)
    return dest, kernelspec_dict


def main():
    """
    Main function for installing or resetting the Jupyter kernelspec for MATLAB Kernel.

    This function parses command-line arguments to determine whether to install
    or reset the kernelspec. It then calls the appropriate functions to perform
    the requested action and prints the result.

    The function supports the following options:
        --reset: Reset the kernelspec to use the standard Python executable.

    If no option is provided, it installs the kernelspec using the current Python executable.

    Raises:
        OSError: If there's a permission error during installation.

    """
    parser = argparse.ArgumentParser(
        prog="install-matlab-kernelspec",
        description="Install or Reset Jupyter kernelspec for MATLAB Kernel",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the kernelspec to the default configuration",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview the changes made to kernelspec",
    )
    args = parser.parse_args()

    kernel_name = str(pathlib.Path(__file__).parent.name)
    if args.reset:
        executable = STANDARD_PYTHON_EXECUTABLE
    else:
        executable = sys.executable

    register_kernelspec_with_jupyter = True
    if args.preview:
        register_kernelspec_with_jupyter = False

    try:
        kernelspec_dir = pathlib.Path(tempfile.mkdtemp()) / kernel_name
        dest, kernelspec_dict = install_kernel_spec(
            kernel_name=kernel_name,
            executable=executable,
            kernelspec_dir=kernelspec_dir,
            register_with_jupyter=register_kernelspec_with_jupyter,
        )
    except OSError as e:
        if e.errno == errno.EACCES:
            print(e, file=sys.stderr)
            sys.exit(1)
        raise

    if args.preview:
        # Replace the destination path to be displayed to the user with the path where the kernelspec would be installed without the dry run mode.
        dest = str(
            pathlib.Path(sys.prefix) / "share" / "jupyter" / "kernels" / kernel_name
        )
        print(
            f"The following kernelspec for {kernel_name} would be installed in {dest}\n{json.dumps(kernelspec_dict, indent=4)}"
        )
        sys.exit(0)

    print(
        f"Installed the following kernelspec for {kernel_name} in {dest}\n{json.dumps(kernelspec_dict, indent=4)}"
    )
