# Copyright 2024 The MathWorks, Inc.

from jupyter_matlab_kernel.magics.base.matlab_magic import MATLABMagic
from jupyter_matlab_kernel.mwi_exceptions import MagicError


class file(MATLABMagic):

    info_about_magic = """Save contents of cell to a specified file in the notebook folder.
Example:
    %%file myfile.m
Save contents of cell to a file named myfile.m in the notebook folder."""

    skip_matlab_execution = True

    def before_cell_execute(self):
        if len(self.parameters) < 1:
            raise MagicError("The file magic expects the name of a file as a argument.")
        elif len(self.parameters) > 1:
            raise MagicError("The file magic expects a single file name as a argument.")
        cell_code = self.cell_code.split("\n")
        # Remove the lines of code before file magic command.
        cell_code = "\n".join(cell_code[self.line_number :])
        if cell_code == "":
            raise MagicError("The cell is empty.")
        try:
            with open(str(self.parameters[0]), "w") as file:
                file.write(cell_code)
        except Exception as e:
            raise MagicError(
                f"An error occurred while creating or writing to the file '{self.parameters[0]}':\n{e}"
            ) from e
        output = f"File {self.parameters[0]} created successfully."
        yield {
            "type": "execute_result",
            "mimetype": ["text/plain", "text/html"],
            "value": [output, f"<html><body><pre>{output}</pre></body></html>"],
        }
