class Conversations:

    def archive_conversation(self, conversation_id):
        response = self._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response
