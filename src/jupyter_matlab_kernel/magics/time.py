# Copyright 2024 The MathWorks, Inc.

import time as timer

from jupyter_matlab_kernel.magics.base.matlab_magic import MATLABMagic
from jupyter_matlab_kernel.mwi_exceptions import MagicError


class time(MATLABMagic):

    info_about_magic = "Display time taken to execute a cell."
    start_time = None

    def format_duration(self, seconds):
        intervals = [
            ("hours", 3600),
            ("minutes", 60),
            ("seconds", 1),
            ("milliseconds", 1e-3),
        ]

        for name, count in intervals:
            if seconds >= count:
                value = seconds / count
                return f"{value:.2f} {name}"

        return f"{seconds * 1e3:.2f} milliseconds"

    def before_cell_execute(self):
        if len(self.parameters) != 0:
            raise MagicError("time magic does not expect any arguments.")
        self.start_time = timer.time()
        yield {}

    def after_cell_execute(self):
        elapsed_time = timer.time() - self.start_time
        formatted_duration = self.format_duration(elapsed_time)
        output = f"Execution of the cell took {formatted_duration} to run."
        yield {
            "type": "execute_result",
            "mimetype": ["text/plain", "text/html"],
            "value": [output, f"<html><body>{output}</body></html>"],
        }
