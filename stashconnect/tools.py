class Tools:
    def __init__(self, client):
        self.client = client

    def get_type(self, type_id):
        """Returns type (conversation or channel)
        Args:
            type_id (int | str): The conversation or channel id
        """
        if type_id == self.client.user_id:
            return "personal"

        conversation_data = {
            "conversation_id": type_id,
            "source": "conversation",
            "limit": 0,
            "offset": 0,
        }
        channel_data = {
            "channel_id": type_id,
            "source": "channel",
            "limit": 0,
            "offset": 0,
        }
        try:
            self.client._post("message/content", data=conversation_data)
            return "conversation"
        except Exception:
            try:
                self.client._post("message/content", data=channel_data)
                return "channel"
            except Exception:
                return "404"
