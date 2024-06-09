class AuthManager:
    def __init__(self, client):
        self.client = client

    def _login(self, email: str, password: str, app_name: str) -> dict:
        """## Logs into a account.

        #### Args:
            email (str): The users email.
            password (str): The users password.
            app_name (str): The app name to be used.

        #### Returns:
            dict: User data.
        """
        data = {
            "email": email,
            "password": password,
            "app_name": app_name,
            "encrypted": "true",
            "callable": "true",
        }

        response = self.client._post("auth/login", data=data, auth=False)
        return response

    def verify_login(
        self, app_name: str = None, encrypted: bool = True, callable: bool = True
    ) -> dict:
        """## Verifies if the user has logged in successfully.

        #### Args:
            app_name (str, optional): The devices app name. Defaults to None.
            encrypted (bool, optional): The devices encryption status. Defaults to True.
            callable (bool, optional): The devices callable status. Defaults to True.

        #### Returns:
            dict: The input args.
        """
        data = {
            "app_name": self.client.app_name if app_name is None else app_name,
            "encrypted": encrypted,
            "callable": callable,
        }

        return data
