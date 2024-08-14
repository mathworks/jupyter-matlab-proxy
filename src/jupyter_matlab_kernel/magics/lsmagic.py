# Copyright 2024 The MathWorks, Inc.

from jupyter_matlab_kernel.magics.base.matlab_magic import MATLABMagic
from jupyter_matlab_kernel.magic_helper import get_magic_names
from jupyter_matlab_kernel.mwi_exceptions import MagicError


class lsmagic(MATLABMagic):

    info_about_magic = "List available magic commands."

    def before_cell_execute(self):
        if len(self.parameters) != 0:
            raise MagicError("The lsmagic magic does not expect any arguments.")
        display_magics = ["%%" + s for s in get_magic_names()]
        output = f"Available magic commands: {display_magics}."
        yield {
            "type": "execute_result",
            "mimetype": ["text/plain", "text/html"],
            "value": [output, f"<html><body>{output}</body></html>"],
        }
