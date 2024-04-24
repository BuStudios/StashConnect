class Tools:

    def get_type(self, id):
        
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
            self._post("message/content", data=conversation_data)
            return "conversation"
        except Exception:
            try:
                self._post("message/content", data=channel_data)
                return "channel"
            except Exception:
                return "404"