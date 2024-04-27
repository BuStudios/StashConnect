class Tools:
    def __init__(self, client):
        self.client = client

    def get_type(self, id):
        """Returns type (conversation or channel)
        Args:
            id (int | str): The conversation or channels id
        """

        conversation_data = {
            "conversation_id": id,
            "source": "conversation",
            "limit": 0,
            "offset": 0,
        }
        channel_data = {
            "channel_id": id,
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
