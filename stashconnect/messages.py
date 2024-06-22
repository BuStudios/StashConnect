import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.Protocol
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto

import Crypto.Random
import Crypto.Util
import Crypto.Util.Padding

import json
from typing import Generator

from .crypto_utils import CryptoUtils
from .models import Message


class MessageManager:
    def __init__(self, client):
        self.client = client

    def send(
        self,
        target: str | int,
        text: str,
        *,
        markdown: bool = True,
        files: str | int | list = None,
        urls: str | list = "",
        location: bool | tuple | list = None,
        encrypted: bool = True,
        **kwargs,
    ) -> Message:
        """## Sends a message.

        #### Args:
            target (str | int): The messages target location.
            text (str): The text to send.
            markdown (bool): Add markdown support. Defaults to True.
            files (str | int | list, optional): Files to send. Defaults to None.
            urls (str | list, optional): Url's to append to the message. Defaults to "".
            location (bool | tuple | list, optional): The location of the message. Defaults to None.
            encrypted (bool, optional): If the message should be encrypted. Defaults to True.

        #### Info:
            :The location needs to be set to (lat, lng) in a tuple or None.

        #### Returns:
            Message: A message object.
        """
        target_type = self.client.tools.get_type(target)

        if encrypted:
            if self.client._private_key is None:
                print(
                    "Could not send encrypted message as no encryption password was provided"
                )
                return

            iv = Crypto.Random.get_random_bytes(16)
            conversation_key = self.client.get_conversation_key(target, target_type)

            text_bytes = text.encode("utf-8")
            text = CryptoUtils.encrypt_aes(text_bytes, conversation_key, iv)

        files_sent = []

        if files is not None:

            if isinstance(files, str | int):
                files = [files]

            for file in files:
                if isinstance(file, str):
                    if file.isnumeric():
                        files_sent.append(int(file))
                    else:
                        file = self.client.files.upload(
                            target, file, encrypted=encrypted
                        )
                        files_sent.append(int(file.id))

                elif isinstance(file, int):
                    files_sent.append(int(file))

                else:
                    file = self.client.files.upload(target, file, encrypted=encrypted)
                    files_sent.append(int(file.id))

        if isinstance(urls, str):
            sent_urls = [urls]
        else:
            sent_urls = urls

        data = {
            "target": target_type,
            f"{target_type}_id": target,
            "text": text,
            "files": json.dumps(files_sent),
            "url": json.dumps(sent_urls),
            "encrypted": encrypted,
            "verification": "",
            "type": "text",
            "is_forwarded": False,
        }

        if encrypted:
            data["iv"] = iv.hex()
            data["text"] = text.hex()

        if markdown:
            data["metainfo"] = json.dumps({"v": 1, "style": "md"})

        data.update(kwargs)

        if location is True:

            location = self.client.account.location()

            if encrypted:
                data["latitude"] = CryptoUtils.encrypt_aes(
                    str(location["latitude"]).encode("utf-8"), conversation_key, iv=iv
                ).hex()
                data["longitude"] = CryptoUtils.encrypt_aes(
                    str(location["longitude"]).encode("utf-8"), conversation_key, iv=iv
                ).hex()
            else:
                data["latitude"] = str(location["latitude"])
                data["longitude"] = str(location["longitude"])

        elif isinstance(location, tuple | list):

            if encrypted:
                data["latitude"] = CryptoUtils.encrypt_aes(
                    str(location[0]).encode("utf-8"), conversation_key, iv=iv
                ).hex()

                data["longitude"] = CryptoUtils.encrypt_aes(
                    str(location[1]).encode("utf-8"), conversation_key, iv=iv
                ).hex()
            else:
                data["latitude"] = str(location[0])
                data["longitude"] = str(location[1])

        data = self.client._post("message/send", data=data)["message"]
        return Message(self.client, data)

    def decode(self, target: str, text: bytes, iv: bytes, key: bytes = None) -> str:
        """## Decode a encrypted message.

        #### Args:
            target (str): The types id.
            text (bytes): The encrypted text.
            iv (bytes): The iv of the text.
            key (bytes, optional): The conversation key. Defaults to None.

        #### Returns:
            str: The decrypted key.
        """
        target_type = self.client.tools.get_type(target)

        if text == "":
            return text
        else:
            try:
                if self.client._private_key is None:
                    return text
                else:
                    conversation_key = self.client.get_conversation_key(
                        target, target_type, key=key
                    )

                    text = CryptoUtils.decrypt_aes(
                        bytes.fromhex(text), conversation_key, bytes.fromhex(iv)
                    )
                    return text.decode("utf-8")
            except Exception:
                return text

    def like(self, message_id: str | int) -> dict:
        """## Likes a message.

        #### Args:
            message_id (str | int): The messages id.

        #### Returns:
            dict: The success status.
        """
        return self.client._post("message/like", data={"message_id": message_id})

    def unlike(self, message_id: str | int) -> dict:
        """## Unlikes a message.

        #### Args:
            message_id (str | int): The messages id.

        #### Returns:
            dict: The success status.
        """
        return self.client._post("message/unlike", data={"message_id": message_id})

    def delete(self, message_id: str | int) -> dict:
        """## Deletes a message.

        #### Args:
            message_id (str | int): The messages id.

        #### Returns:
            dict: The succes status.
        """
        return self.client._post("message/delete", data={"message_id": message_id})

    def infos(self, message_ids: str | int | list) -> dict:
        """## Gets the infos of messages.

        #### Args:
            message_ids (str | int | list): The message ids.

        #### Returns:
            dict: The message infos
        """
        if isinstance(message_ids, str | int):
            ids = [message_ids]
        else:
            ids = message_ids
        messages = self.client._post(
            "message/infos", data={"message_ids": json.dumps(ids)}
        )
        return [Message(self.client, message) for message in messages["messages"]]

    def get_messages(
        self, type_id: str | int, limit: int = 30, offset: int = 0
    ) -> Generator[Message, None, None]:
        """## Gets the messages of a channel or conversation.

        #### Args:
            type_id (str | int): The types id
            limit (int, optional): The responses limit. Defaults to 30.
            offset (int, optional): The responses offset. Defaults to 0.

        #### Yields:
            Generator[Message, None, None]: Message objects.
        """
        target_type = self.client.tools.get_type(type_id)

        data = {
            f"{target_type}_id": type_id,
            "source": target_type,
            "limit": limit,
            "offset": offset,
        }

        response = self.client._post("message/content", data=data)
        response = response["messages"]

        for message in response:
            if message["kind"] != "message":
                continue

            yield Message(self.client, message)

    def get_flagged(
        self, type_id: str | int, limit: int = 100, offset: int = 0
    ) -> Generator[Message, None, None]:
        """## Gets the flagged messages of a channel.

        #### Args:
            type_id (str | int): The types id.
            limit (int, optional): The responses limit. Defaults to 100.
            offset (int, optional): The responses offset. Defaults to 0.

        #### Yields:
            Generator[Message, None, None]: Message objects.
        """
        target_type = self.client.tools.get_type(type_id)

        data = {
            "type": target_type,
            "type_id": type_id,
            "offset": offset,
            "limit": limit,
        }

        response = self.client._post("message/list_flagged_messages", data=data)
        response = response["messages"]

        for message in response:
            if message["kind"] != "message":
                continue

            yield Message(self.client, message)

    def flag(self, message_id: str | int) -> dict:
        """## Flags a message.

        #### Args:
            message_id (str | int): The messages id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post("message/flag", data={"message_id": message_id})
        return response

    def unflag(self, message_id: str | int) -> dict:
        """## Unflags a message.

        #### Args:
            message_id (str | int): The messages id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post("message/unflag", data={"message_id": message_id})
        return response
