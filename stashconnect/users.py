import requests
from PIL import Image
import io
import base64


class UserManager:
    def __init__(self, client):
        self.client = client

    def change_profile_picture(self, *, url: str):
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
            return response

    def reset_profile_picture(self):
        response = self.client._post("account/reset_profile_image", data={})
        return response

    def change_status(self, status: str):
        response = self.client._post("account/change_status", data={"status": status})
        return response

    def get_location(self):
        response = self.client._post("/location/get", data={})
        return response


class User:
    def __init__(self, client, data) -> None:
        self.client = client
        self.id = data["id"]
        user = self.client._post(
            "users/info", data={"user_id": data["id"], "withkey": True}
        )["user"]
        self.first_name = user["first_name"]
        self.last_name = user["last_name"]
        
        self.email = user["email"]
        self.status = user["status"]
        self.image = user["image"]
        
        self.language = user["language"]
        self.last_login = user["last_login"]
        self.online = user["online"]
        self.permissions = user["permissions"]
        
        self.public_key = user["public_key"]
        self.companies = user["roles"]
