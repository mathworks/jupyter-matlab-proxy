# Copyright 2026 The MathWorks, Inc.

from abc import ABC, abstractmethod


# Abstract Action class which other actions are meant to implement.
class ActionCommand(ABC):
    @abstractmethod
    async def execute(self, comm, data):
        """Runs the action and sends its result back to the lab extension.

        This is the single entry point invoked by the comm layer for a given
        action type. Concrete actions should validate ``data`` (typically via
        :meth:`validate_data`), perform their work, and report the outcome by
        calling ``comm.send(...)`` — both on success and on failure — rather
        than raising, so the lab extension always receives a response.

        Args:
            comm (ipykernel.comm.Comm): Communication channel used to send the
                result payload back to the lab extension.
            data (dict): Action-specific payload received from the lab
                extension.
        """
        pass

    def get_code(self, *args):
        """Builds the MATLAB code snippet this action needs to run in MATLAB.

        Only actions that drive MATLAB (e.g. opening a file in the editor)
        override this; actions that run purely on the kernel side leave it
        unimplemented.

        Args:
            *args: Action-specific values used to construct the code.

        Returns:
            str: The MATLAB code to execute.
        """
        pass

    def validate_data(self, data):
        """Validates the payload received from the lab extension.

        Concrete actions override this to assert that all required keys are
        present in ``data``, raising :class:`ValueError` when the payload is
        malformed so :meth:`execute` can report the error to the lab extension.

        Args:
            data (dict): Action-specific payload to validate.

        Raises:
            ValueError: If ``data`` is missing required fields.
        """
        pass
