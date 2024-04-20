import requests
from PIL import Image
import io
import base64


class Users:

    def change_profile_picture(self, *, url):

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

            response = self._post(
                "account/store_profile_image",
                data={"imgBase64": f"data:image/png;base64,{image_base64}"},
            )
            return response

    def reset_profile_picture(self):

        response = self._post("account/reset_profile_image", data={})
        return response

    def change_status(self, status):

        response = self._post("account/change_status", data={"status": status})
        return response

    def get_location(self):

        response = self._post("/location/get", data={})
        return response
