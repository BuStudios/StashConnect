from .crypto_utils import CryptoUtils


class Conversations:

    def archive_conversation(self, conversation_id):

        response = self._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )

        return response

    def get_messages(self, conversation_id, limit=30, offset=0):

        data = {
            "conversation_id": conversation_id,
            "source": "conversation",
            "limit": limit,
            "offset": offset,
        }

        response = self._post("message/content", data=data)
        response = response["messages"]

        conversation_key = self.get_conversation_key(target=conversation_id)

        messages = []

        for message in response:

            if message["location"]["encrypted"]:

                longitude = CryptoUtils.decrypt_aes(
                    bytes.fromhex(message["location"]["longitude"]),
                    conversation_key,
                    iv=bytes.fromhex(message["location"]["iv"]),
                ).decode("utf-8")

                latitude = CryptoUtils.decrypt_aes(
                    bytes.fromhex(message["location"]["latitude"]),
                    conversation_key,
                    iv=bytes.fromhex(message["location"]["iv"]),
                ).decode("utf-8")

            else:

                longitude = message["location"]["longitude"]
                latitude = message["location"]["latitude"]

            messages.append(
                {
                    "text": self.decode_message(
                        target=message["conversation_id"],
                        text=message["text"],
                        iv=message["iv"],
                    ),
                    "time": message["time"],
                    "location": {"longitude": longitude, "latitude": latitude},
                }
            )

        return messages
