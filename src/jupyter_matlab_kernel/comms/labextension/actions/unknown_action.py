# Copyright 2026 The MathWorks, Inc.

from . import ActionCommand


class UnknownAction(ActionCommand):
    def __init__(self, kernel):
        self.kernel = kernel
        self.log = kernel.log

    async def execute(self, comm, data):
        raise Exception("Unknown action")
