# Copyright 2026 The MathWorks, Inc.

from . import ActionCommand, ActionTypes


class MatlabStatusAction(ActionCommand):
    def __init__(self, kernel):
        self.kernel = kernel
        self.log = kernel.log

    async def execute(self, comm, data):
        try:
            self.log.debug("Fetching MATLAB proxy status...")
            status = await self.kernel.mwi_comm_helper.fetch_matlab_proxy_status()

            self.log.debug(
                f"MatlabStatus action successful.Licensing Status: '{status.is_matlab_licensed}', Status: '{status.matlab_status}' "
            )
            comm.send(
                {
                    "action": ActionTypes.MATLAB_STATUS.value,
                    "data": status.to_dict(camel_case=True),
                    "error": None,
                }
            )
        except Exception as err:
            self.log.error(f"Error fetching MATLAB proxy status: {err}")
            comm.send(
                {
                    "action": ActionTypes.MATLAB_STATUS.value,
                    "data": None,
                    "error": str(err),
                }
            )
