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

from .crypto_utils import CryptoUtils
from .models import Message


class MessageManager:
    def __init__(self, client):
        self.client = client

    def send(
        self,
        target,
        text: str,
        *,
        files=None,
        url="",
        location: bool | tuple | list = None,
        encrypted: bool = True,
        **kwargs,
    ):
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
                files_sent = [files]

            for file in files:
                file = self.client.upload_file(target, file, encrypted)
                files_sent.append(int(file["id"]))

        url = [url]

        data = {
            "target": target_type,
            f"{target_type}_id": target,
            "text": text,
            "files": json.dumps(files_sent),
            "url": json.dumps(url),
            "encrypted": encrypted,
            "verification": "",
            "type": "text",
            "is_forwarded": False,
        }

        if encrypted:
            data["iv"] = iv.hex()
            data["text"] = text.hex()

        data.update(kwargs)

        if location is True:

            location = self.client.get_location()["location"]

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

    def decode(self, target, text, iv, key=None):
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

    def like(self, message_id):
        return self.client._post("message/like", data={"message_id": message_id})

    def unlike(self, message_id):
        return self.client._post("message/unlike", data={"message_id": message_id})

    def delete(self, message_id):
        return self.client._post("message/delete", data={"message_id": message_id})

    def infos(self, message_ids):
        if isinstance(message_ids, str | int):
            ids = [message_ids]
        else:
            ids = message_ids
        messages = self.client._post(
            "message/infos", data={"message_ids": json.dumps(ids)}
        )
        return messages["messages"]

    def get_messages(self, conversation_id, limit: int = 30, offset: int = 0):
        target_type = self.client.tools.get_type(conversation_id)

        data = {
            f"{target_type}_id": conversation_id,
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

    def get_flagged(self, conversation_id, limit: int = 100, offset: int = 0):
        target_type = self.client.tools.get_type(conversation_id)

        data = {
            "type": target_type,
            "type_id": conversation_id,
            "offset": offset,
            "limit": limit,
        }

        response = self.client._post("message/list_flagged_messages", data=data)
        response = response["messages"]

        for message in response:
            if message["kind"] != "message":
                continue

            yield Message(self.client, message)

    def flag(self, message_id):
        response = self.client._post("message/flag", data={"message_id": message_id})
        return response

    def unflag(self, message_id):
        response = self.client._post("message/unflag", data={"message_id": message_id})
        return response
