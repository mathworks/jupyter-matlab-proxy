# Copyright 2025 The MathWorks, Inc.

"""A custom hatch build hook for jupyter_matlab_kernel."""

import json
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class KernelSpecBuilderHook(BuildHookInterface):
    """A custom build hook for jupyter_matlab_kernel to generate the kernel.json file."""

    def initialize(self, version, build_data):
        """Initialize the hook."""
        parent_dir = Path(__file__).parent.resolve()

        # Add the src directory to the system path to import the get_kernel_spec function
        sys.path.insert(0, str(parent_dir / "src"))
        from jupyter_matlab_kernel.kernelspec import get_kernel_spec

        kernelspec_json = get_kernel_spec(executable="python3")

        dest = (
            parent_dir / "src" / "jupyter_matlab_kernel" / "kernelspec" / "kernel.json"
        )
        if dest.exists():
            dest.unlink()

        with open(dest, "w") as f:
            json.dump(kernelspec_json, f, indent=4)
