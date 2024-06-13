import Crypto
import Crypto.Random
import Crypto.Util

import os
import mimetypes
import uuid
from PIL import Image
import base64
import io
import json

from .crypto_utils import CryptoUtils
from .models import Channel, Conversation, File


class FileManager:
    def __init__(self, client):
        self.client = client

    def quota(self) -> dict:
        """## Gets the users quota.

        #### Returns:
            dict: The users quota.
        """
        response = self.client._post(
            "file/quota", data={"type": "personal", "type_id": self.client.user_id}
        )
        return response["quota"]

    def upload(
        self,
        target: str | int,
        filepath: str,
        encrypted: bool = True,
        preview: bool = True,
    ) -> File:
        """## Uploads a file to a target location.

        #### Args:
            target (str | int): The upolads target id.
            filepath (str): The files location path.
            encrypted (bool, optional): Sets whether a file should be encrypted. Defaults to True.
            preview (bool, optional): Sets whether a preview image should be set. Defaults to True.

        #### Returns:
            File: A file object.
        """
        filename = os.path.basename(filepath)

        if encrypted:
            if self.client._private_key is None:
                print(
                    "Could not upload encrypted file as no encryption password was provided"
                )
                return

            # generate random iv and file key
            iv = Crypto.Random.get_random_bytes(16)
            file_key = Crypto.Random.get_random_bytes(32)

        # guess content type from extension
        content_type = mimetypes.guess_type(filepath)[0]
        if not content_type:
            content_type = "application/octet-stream"

        max_chunk_size = 5 * 1024 * 1024  # limit chunk upload size to 5MB
        upload_identifier = str(uuid.uuid4())  # the uploads id

        # open file in binary mode
        with open(filepath, "rb") as file:
            file_content = file.read()

        try:
            with Image.open(filepath) as image:
                image_width = image.width
                image_height = image.height
        except Exception:
            image_width = None
            image_height = None

        # calculate total chunks
        total_chunks = (len(file_content) + max_chunk_size - 1) // max_chunk_size
        target_type = self.client.tools.get_type(target)

        for i in range(total_chunks):
            data_chunk = file_content[i * max_chunk_size : (i + 1) * max_chunk_size]

            # encrypt the chunk
            if encrypted:
                encrypted_chunk = CryptoUtils.encrypt_aes(data_chunk, file_key, iv)
            else:
                encrypted_chunk = data_chunk

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
                "encrypted": encrypted,
                "media_width": image_width,
                "media_height": image_height,
            }

            if encrypted:
                data["iv"] = iv.hex()

            files = {
                "file": ("[object Object]", encrypted_chunk, "application/octet-stream")
            }

            # upload the current chunk
            response = self.client._post("file/upload", data=data, files=files)
            file = response["file"]

        file_id = file["id"]

        if encrypted:
            # sets a file access key for encrypted files

            iv = Crypto.Random.get_random_bytes(16)

            data = {
                "file_id": file_id,
                "target": target_type,
                "target_id": target,
                "key": CryptoUtils.encrypt_aes(
                    file_key, self.client.get_conversation_key(target, target_type), iv
                ).hex(),
                "iv": iv.hex(),
            }

            response = self.client._post("security/set_file_access_key", data=data)

        if preview:
            self.client.files.store_preview_image(file_id, filepath)

        return File(self.client, file)

    def store_preview_image(self, file_id: str | int, filepath: str) -> File | dict:
        """## Stores a preview image for a file.

        #### Args:
            file_id (str | int): The files id.
            filepath (str): The images file path.

        #### Returns:
            File | dict: A file object or a status: false dict.
        """
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

            response = self.client._post("file/storePreviewImage", data=data)
            return File(self.client, response["file"])

        except Exception:
            return {"success": False}

    def download(self, id: str | int, directory: str = "", filename: str = None) -> str:
        """## Downloads a file to a local location.

        #### Args:
            id (str | int): The files id.
            directory (str, optional): The download dir. Defaults to main.
            filename (str, optional): The new filename. Defaults to the main name.

        #### Returns:
            str: The path of the saved file.
        """
        response = self.client._post(f"file/download?id={id}", data={}, return_all=True)

        if filename is None:
            file_info = self.client.files._info(id)
            file_path = os.path.join(directory, file_info["name"])
        else:
            file_info = self.client.files._info(id)
            file_path = os.path.join(directory, filename + "." + file_info["ext"])

        with open(file_path, "wb") as file:

            if file_info["encrypted"]:
                if self.client._private_key is None:
                    print(
                        "Could not download encrypted content as no encryption password was provided"
                    )
                    return

                key = CryptoUtils.decrypt_aes(
                    bytes.fromhex(file_info["keys"][0]["key"]),
                    self.client.get_conversation_key(
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

        return file_path

    def download_bytes(self, id: str | int) -> bytes:
        """## Downloads a file and returns its content as bytes.

        #### Args:
            id (str | int): The file's id.

        #### Returns:
            str: The path of the saved file.
        """
        response = self.client._post(f"file/download?id={id}", data={}, return_all=True)
        file_info = self.client.files._info(id)

        if file_info["encrypted"]:
            if self.client._private_key is None:
                print(
                    "Could not download encrypted content as no encryption password was provided"
                )
                return

            key = CryptoUtils.decrypt_aes(
                bytes.fromhex(file_info["keys"][0]["key"]),
                self.client.get_conversation_key(
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
            return decrypted
        else:
            return response.content

    def _info(self, id: str | int) -> dict:
        """## Fetches the info of a file (dict).

        #### Args:
            id (str | int): The files id.

        #### Returns:
            dict: The files dict.
        """
        response = self.client._post("file/info", data={"file_id": id})
        return response["file"]

    def info(self, id: str | int) -> File:
        """## Fetches the info of a file.

        #### Args:
            id (str | int): The files id.

        #### Returns:
            File: A file object.
        """
        response = self.client._post("file/info", data={"file_id": id})
        return File(self.client, response["file"])

    def infos(self, ids: str | int | list) -> list:
        """## Fetches mutliple files.

        #### Args:
            ids (str | int | list): The files ids.

        #### Returns:
            list: A list of files.
        """
        ids_sent = []

        if isinstance(ids, str | int):
            ids_sent = [ids]
        else:
            ids_sent = ids

        response = self.client._post(
            "file/infos", data={"file_ids": json.dumps(ids_sent)}
        )

        files = [File(self.client, file) for file in response["files"]]
        return files

    def delete(self, ids: str | int | list) -> dict:
        """## Deletes specified files.

        #### Args:
            ids (str | int | list): The file or files ids

        #### Returns:
            dict: The success status.
        """

        ids_sent = []

        if isinstance(ids, str | int):
            ids_sent = [ids]
        else:
            ids_sent = ids

        response = self.client._post(
            "file/delete", data={"file_ids": json.dumps(ids_sent)}
        )
        return response

    def move(self, id: str | int, folder_id: str | int) -> dict:
        """## Moves a file into a specified folder.

        #### Args:
            id (str | int): The files id.
            folder_id (str | int): The folders id.

        #### Returns:
            dict: The success status.
        """
        data = {"file_id": id, "parent_id": folder_id}
        response = self.client._post("file/move", data=data)
        return response

    def rename(self, id: str | int, name: str) -> dict:
        """## Renames a file.

        #### Args:
            id (str | int): The files id.
            name (str): The files new name.

        #### Returns:
            dict: The success status
        """
        data = {"file_id": id, "name": name}
        response = self.client._post("file/rename", data=data)
        return response

    def copy(
        self,
        id: str | int,
        folder_id: str | int = 0,
        type_id: str | int = None,
    ) -> File:
        """## Copies a file to a folder.

        #### Args:
            id (str | int): The files id.
            folder_id (str | int, optional): The new folders id. Defaults to main.
            type (str, optional): The destinations type. Defaults to "personal".
            type_id (str | int, optional): The destinations type id. Defaults to client.user_id.

        #### Returns:
            File: A file object.
        """
        if type_id is None:
            type_id = self.client.user_id

        target_type = self.client.tools.get_type(type_id)

        data = {
            "file_id": id,
            "folder_id": folder_id,
            "type": target_type,
            "type_id": type_id,
        }
        response = self.client._post("file/copy", data=data)
        return File(self.client, response["file"])

    def shares(self, id: str | int) -> dict:
        """## Get a files shares.

        #### Args:
            id (str | int): The files id.

        #### Returns:
            dict: The files shares as a dict.
        """
        data = {"file_id": id}
        response = self.client._post("file/shares", data=data)["shares"]

        channels = []
        for channel in response["channels"]:
            channels.append(Channel(self.client, channel))

        conversations = []
        for conversation in response["conversations"]:
            conversations.append(Conversation(self.client, conversation))

        response["channels"] = channels
        response["conversations"] = conversations

        return response

    def get(
        self,
        folder_id: str | int = 0,
        type_id: str | int = None,
        folder_only: str = "no",
        offset: int | str = 0,
        limit: int | str = 75,
        search: str = None,
        sorting: str = "created_asc",
    ) -> dict:
        """## Gets the files and folders in a dir.

        #### Args:
            folder_id (str | int, optional): The folders id. Defaults to 0 (personal).
            type_id (str | int, optional): The type id. Defaults to None.
            folder_only (str, optional): Folder only response. Defaults to "no".
            offset (int | str, optional): The response offset. Defaults to 0.
            limit (int | str, optional): The response limit. Defaults to 75.
            search (str, optional): The search prompt. Defaults to None.
            sorting (str, optional): The sorting setting. Defaults to "created_asc".

        #### Returns:
            dict: A dictonary containing folder and file objects.
        """
        if type_id is None:
            type_id = self.client.user_id

        target_type = self.client.tools.get_type(type_id)
        data = {
            "folder_id": folder_id,
            "type": target_type,
            "type_id": type_id,
            "folder_only": folder_only,
            "offset": offset,
            "limit": limit,
            "search": search,
            "sorting": sorting,
        }

        response = self.client._post("folder/get", data=data)
        return response["content"]
