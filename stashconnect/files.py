import Crypto
import Crypto.Random
import Crypto.Util

import os
import mimetypes
import uuid
from PIL import Image
import base64
import io

from .crypto_utils import CryptoUtils


class Files:

    def quota(self):
        response = self._post(
            "file/quota", data={"type": "personal", "type_id": self.user_id}
        )
        return response["quota"]

    def upload_file(self, target, filepath):
        filename = os.path.basename(filepath)

        iv = Crypto.Random.get_random_bytes(16)
        file_key = Crypto.Random.get_random_bytes(32)

        content_type = mimetypes.guess_type(filepath)[0]
        if not content_type:
            content_type = "application/octet-stream"

        max_chunk_size = 5 * 1024 * 1024
        upload_identifier = str(uuid.uuid4())

        with open(filepath, "rb") as file:
            file_content = file.read()

        try:
            with Image.open(filepath) as image:
                image_width = image.width
                image_height = image.height
        except Exception:
            image_width = None
            image_height = None

        total_chunks = (len(file_content) + max_chunk_size - 1) // max_chunk_size
        target_type = self.get_type(target)

        for i in range(total_chunks):
            data_chunk = file_content[i * max_chunk_size : (i + 1) * max_chunk_size]
            encrypted_chunk = CryptoUtils.encrypt_aes(data_chunk, file_key, iv)

            data = {
                "resumableChunkNumber": i,
                "resumableChunkSize": max_chunk_size,
                "resumableCurrentChunkSize": len(encrypted_chunk),
                "resumableTotalSize": len(file_content),
                "resumableType": content_type,
                "resumableIdentifier": upload_identifier,
                "resumableFilename": filename,
                "resumableRelativePath": filename,
                "resumableTotalChunks": total_chunks,
                "folder": 0,
                "type": target_type,
                "type_id": target,
                "encrypted": True,
                "iv": iv.hex(),
                "media_width": image_width,
                "media_height": image_height,
            }

            files = {
                "file": ("[object Object]", encrypted_chunk, "application/octet-stream")
            }

            response = self._post("file/upload", data=data, files=files)
            file = response["file"]

        file_id = file["id"]
        iv = Crypto.Random.get_random_bytes(16)

        data = {
            "file_id": file_id,
            "target": target_type,
            "target_id": target,
            "key": CryptoUtils.encrypt_aes(
                file_key, self.get_conversation_key(target, target_type), iv
            ).hex(),
            "iv": iv.hex(),
        }

        response = self._post("security/set_file_access_key", data=data)

        try:
            with Image.open(filepath) as image:
                output_size = 100

                image = image.convert("RGB")
                min_dimension = min(image.width, image.height)
                scale_factor = output_size / min_dimension

                new_width = int(image.width * scale_factor)
                new_height = int(image.height * scale_factor)

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left, top = (new_width - output_size) / 2, (
                    new_height - output_size
                ) / 2
                right, bottom = left + output_size, top + output_size

                image = image.crop((left, top, right, bottom))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")

                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            data = {
                "file_id": file_id,
                "content": str("data:image/jpeg;base64," + image_base64),
            }

            self._post("file/storePreviewImage", data=data)

        except Exception:
            pass

        return file

    def download_file(self, id, directory):
        response = self._post(f"file/download?id={id}", data={}, return_all=True)

        file_info = self.file_info(id)
        file_path = os.path.join(directory, file_info["name"])

        with open(file_path, "wb") as file:

            if file_info["encrypted"]:
                key = CryptoUtils.decrypt_aes(
                    bytes.fromhex(file_info["keys"][0]["key"]),
                    self.get_conversation_key(
                        file_info["keys"][0]["chat_id"],
                        file_info["keys"][0]["type"],
                        key=file_info["keys"][0]["chat_key"],
                    ),
                    bytes.fromhex(file_info["keys"][0]["iv"]),
                )
                decrypted = CryptoUtils.decrypt_aes(
                    response.content,
                    key,
                    bytes.fromhex(file_info["e2e_iv"]),
                )
                file.write(decrypted)
            else:
                file.write(response.content)

        return {"success": True}

    def file_info(self, id):
        response = self._post("file/info", data={"file_id": id})
        return response["file"]
