# Copyright 2024 The MathWorks, Inc.

import importlib
from pathlib import Path


def get_magic_names():
    """
    Lists the names of all the magic commands.

    Returns:
    [str]: All the available magics.
    """
    module_name = __name__
    module_spec = importlib.util.find_spec(module_name)
    magic_names = []
    if module_spec and module_spec.origin:
        magic_path = Path(module_spec.origin).parent / "magics"
        magic_names = [
            s.replace(".py", "")
            for s in [
                f.name
                for f in magic_path.iterdir()
                if f.is_file() and f.name.endswith(".py")
            ]
        ]
    return magic_names
