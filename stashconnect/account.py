from PIL import Image
import requests
import io
import base64

from .models import User


class AccountManager:
    def __init__(self, client):
        self.client = client

    def change_status(self, status: str) -> dict:
        """## Changes the users status.

        #### Args:
            status (str): The new status

        #### Returns:
            dict: The new status.
        """
        response = self.client._post("account/change_status", data={"status": status})
        return response

    def change_email(self, email: str) -> dict:
        """## Changes the users email.

        #### Args:
            email (str): The new email.

        #### Returns:
            dict: The new email.
        """
        response = self.client._post("/account/change_email", data={"email": email})
        return response

    def resend_validation_email(self, email: str) -> str:
        """## Resends a validation email.

        #### Args:
            email (str): The used email.

        #### Returns:
            str: The success status.
        """
        response = self.client._post(
            "/register/resend_validation_email", data={"email": email}
        )
        return response

    def change_password(self, new_password: str, old_password: str) -> dict:
        """## Changes a users password.

        #### Args:
            new_password (str): The new password.
            old_password (str): The old password.

        #### Returns:
            dict: The success status.
        """
        data = {"new_password": new_password, "old_password": old_password}
        response = self.client._post("/account/change_password", data=data)
        return response

    def settings(self) -> dict:
        """## Gets the users settings.

        #### Returns:
            dict: The settings
        """
        response = self.client._post("/account/settings", data={})
        return response["settings"]

    def active_devices(self) -> dict:
        """## Gets a users active devices.

        #### Returns:
            dict: The active devices.
        """
        response = self.client._post("/account/list_active_devices", data={})
        return response["devices"]

    def notifications(self, limit: int = 20, offset: int = 0) -> dict:
        """## Gets a users notifications.

        #### Args:
            limit (int, optional): The response limit. Defaults to 20.
            offset (int, optional): The response offset. Defaults to 0.

        #### Returns:
            dict: The notifications.
        """
        data = {"limit": limit, "offset": offset}
        response = self.client._post("notifications/get", data=data)
        return response["notifications"]

    def notification_count(self) -> int:
        """## Gets the notification count.

        #### Returns:
            int: The notification count.
        """
        response = self.client._post("notifications/count", data={})
        return int(response["count"])

    def location(self) -> dict:
        """## Gets the users location information.

        #### Returns:
            dict: The information.
        """
        response = self.client._post("/location/get", data={})
        return response["location"]

    def reset_profile_picture(self) -> dict:
        """## Resets the users profile picture.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post("account/reset_profile_image", data={})
        return response

    def change_profile_picture(self, url: str) -> User:
        """## Changes the users profile picture.

        #### Args:
            url (str): A image url.

        #### Returns:
            User: A user object.
        """
        response = requests.get(url)
        response.raise_for_status()

        with Image.open(io.BytesIO(response.content)) as image:

            min_dimension = min(image.width, image.height)
            scale_factor = 512 / min_dimension

            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left, top = (new_width - 512) / 2, (new_height - 512) / 2
            right, bottom = left + 512, top + 512
            image = image.crop((left, top, right, bottom))

            buffered = io.BytesIO()
            image.save(buffered, format="PNG")

            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            response = self.client._post(
                "account/store_profile_image",
                data={"imgBase64": f"data:image/png;base64,{image_base64}"},
            )

            return User(self.client, response["user"])
