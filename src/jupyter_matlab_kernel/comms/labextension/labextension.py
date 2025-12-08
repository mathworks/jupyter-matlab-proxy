# Copyright 2025 The MathWorks, Inc.

from ipykernel.comm import Comm


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
        action_type, action_data = payload["action"], payload["data"]

        self.log.debug(
            f"Received action_type:{action_type} with data:{action_data} from the lab extension"
        )

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
