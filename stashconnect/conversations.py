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


class Conversations:

    def archive_conversation(self, conversation_id):
        response = self._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response

    def get_messages(self, conversation_id, limit=30, offset=0):
        data = {
            "conversation_id": conversation_id,
            "source": "conversation",
            "limit": limit,
            "offset": offset,
        }

        response = self._post("message/content", data=data)
        response = response["messages"]
        conversation_key = self.get_conversation_key(target=conversation_id)

        messages = []

        for message in response:
            if message["location"]["encrypted"]:

                longitude = CryptoUtils.decrypt_aes(
                    bytes.fromhex(message["location"]["longitude"]),
                    conversation_key,
                    iv=bytes.fromhex(message["location"]["iv"]),
                ).decode("utf-8")

                latitude = CryptoUtils.decrypt_aes(
                    bytes.fromhex(message["location"]["latitude"]),
                    conversation_key,
                    iv=bytes.fromhex(message["location"]["iv"]),
                ).decode("utf-8")
            else:
                longitude = message["location"]["longitude"]
                latitude = message["location"]["latitude"]

            messages.append(
                {
                    "text": self.decode_message(
                        target=message["conversation_id"],
                        text=message["text"],
                        iv=message["iv"],
                    ),
                    "time": message["time"],
                    "location": {"longitude": longitude, "latitude": latitude},
                }
            )
        return messages

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

        total_chunks = (len(file_content) + max_chunk_size - 1) // max_chunk_size

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
                "type": "conversation",
                "type_id": target,
                "encrypted": True,
                "iv": iv.hex(),
                "media_width": 100,  # change this
                "media_height": 100,  # change this
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
            "target": "conversation",
            "target_id": target,
            "key": CryptoUtils.encrypt_aes(
                file_key, self.get_conversation_key(target), iv
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