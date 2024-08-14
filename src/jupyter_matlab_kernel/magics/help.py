# Copyright 2024 The MathWorks, Inc.

from jupyter_matlab_kernel.magics.base.matlab_magic import MATLABMagic
from jupyter_matlab_kernel.magic_helper import get_magic_names
from jupyter_matlab_kernel.mwi_exceptions import MagicError
import importlib


class help(MATLABMagic):

    info_about_magic = "Provide information about the specified magic command."

    def before_cell_execute(self):
        if len(self.parameters) != 1:
            raise MagicError(
                "The help magic expects a single magic name as a argument."
            )
        magic_name = self.parameters[0]
        output = ""
        magics_info = self.__get_help(magic_name)
        if magics_info:
            output = output + f"{magic_name} Magic: {magics_info}\n"
        if output == "":
            raise MagicError(f"The Magic {magic_name} does not exist.")
        yield {
            "type": "execute_result",
            "mimetype": ["text/plain", "text/html"],
            "value": [output, f"<html><body><pre>{output}</pre></body></html>"],
        }

    def do_complete(self, parameters, parameter_pos, cursor_pos):
        matches = []
        if parameter_pos == 1:
            if cursor_pos == 0:
                matches = get_magic_names()
            else:
                matches = [
                    s
                    for s in get_magic_names()
                    if s.startswith(parameters[0][:cursor_pos])
                ]
        return matches

    def __get_help(self, module_name):

        full_module_name = f"jupyter_matlab_kernel.magics.{module_name}"
        print(full_module_name)

        try:
            module = importlib.import_module(full_module_name)

            if hasattr(module, module_name):
                magic_class = getattr(module, module_name)
                return magic_class.get_info_about_magic()
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error using help magic: {e}")
            return None
