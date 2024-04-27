import Crypto
import Crypto.Random
import Crypto.Util

from .crypto_utils import CryptoUtils


class Conversations:
    def __init__(self, client):
        self.client = client

    def archive_conversation(self, conversation_id):
        response = self.client._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response
