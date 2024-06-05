from .models import User


class UserManager:
    def __init__(self, client):
        self.client = client

    def _info(self, user_id, withkey=True):
        response = self.client._post(
            "users/info", data={"user_id": user_id, "withkey": withkey}
        )
        return response["user"]

    def info(self, user_id, withkey=True):
        response = self.client._post(
            "users/info", data={"user_id": user_id, "withkey": withkey}
        )
        return User(self.client, response["user"])

    def me(self):
        response = self.client._post("users/me", data={})
        return User(self.client, response["user"])
