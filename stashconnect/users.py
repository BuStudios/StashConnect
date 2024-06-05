from .models import User


class UserManager:
    def __init__(self, client):
        self.client = client

    def _info(self, user_id: str | int, withkey: bool = True) -> dict:
        """## Gets a users user info as a dict.

        #### Args:
            user_id (str | int): The users id
            withkey (bool, optional): Return key. Defaults to True.

        #### Returns:
            dict: A user as a dict.
        """
        response = self.client._post(
            "users/info", data={"user_id": user_id, "withkey": withkey}
        )
        return response["user"]

    def info(self, user_id: str | int, withkey: bool = True) -> User:
        """## Gets a users user info.

        #### Args:
            user_id (str | int): The users id
            withkey (bool, optional): Return key. Defaults to True.

        #### Returns:
            User: A user object.
        """
        response = self.client._post(
            "users/info", data={"user_id": user_id, "withkey": withkey}
        )
        return User(self.client, response["user"])

    def me(self) -> User:
        """## Gets the clients user object.

        #### Returns:
            User: A user object.
        """
        response = self.client._post("users/me", data={})
        return User(self.client, response["user"])
