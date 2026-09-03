# Copyright 2025-2026 The MathWorks, Inc.

from ipykernel.comm import Comm
from jupyter_matlab_kernel.comms.labextension.actions.action_factory import (
    ActionFactory,
)


class LabExtensionCommunication:
    def __init__(self, kernel):
        self.comms = {}
        self.kernel = kernel
        self.log = kernel.log

    def comm_open(self, stream, ident, msg):
        """Handler to execute when labextension sends a message with 'comm_open' type ."""

        # As per jupyter messaging protocol https://jupyter-client.readthedocs.io/en/latest/messaging.html#custom-messages
        # 'content' will be present in msg, 'comm_id' and 'target_name' will be present in content.

        content = msg["content"]
        comm_id = content["comm_id"]
        target_name = content["target_name"]
        self.log.debug(
            f"Received comm_open message with id: {comm_id} and target_name: {target_name}"
        )
        comm = Comm(comm_id=comm_id, primary=False, target_name=target_name)
        self.comms[comm_id] = comm
        self.log.debug(
            f"Successfully created communication channel with labextension on: {comm_id}"
        )

    async def comm_msg(self, stream, ident, msg):
        """Handler to execute when labextension sends a message with 'comm_msg' type."""
        # As per jupyter messaging protocol https://jupyter-client.readthedocs.io/en/latest/messaging.html#custom-messages
        # 'content' will be present in msg, 'comm_id' and 'data' will be present in content.
        payload = msg["content"]["data"]
        comm_id = msg["content"]["comm_id"]
        action_type, action_data = payload["action"], payload["data"]

        comm = self.comms.get(comm_id)

        if comm is None:
            self.log.error(
                f"Received comm_msg for unknown comm_id: {comm_id}. Ignoring message."
            )
            return

        self.log.debug(
            f"Received action_type:{action_type} with data:{action_data} from the lab extension"
        )

        action = ActionFactory.create_action(action_type, self.kernel)
        self.log.debug(f"Action to execute is {action.__class__.__name__}")

        try:
            await action.execute(comm, action_data)

        except Exception as err:
            self.log.error(f"Failed to execute action with exception: {err}")

    def comm_close(self, stream, ident, msg):
        """Handler to execute when labextension sends a message with 'comm_close' type."""

        # As per jupyter messaging protocol https://jupyter-client.readthedocs.io/en/latest/messaging.html#custom-messages
        # 'content' will be present in msg, 'comm_id' and 'data' will be present in content.
        content = msg["content"]
        comm_id = content["comm_id"]
        comm = self.comms.get(comm_id)

        if comm:
            self.log.info(f"Comm closed with id: {comm_id}")
            del self.comms[comm_id]

        else:
            self.log.debug(f"Attempted to close unknown comm_id: {comm_id}")
