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
from .users import User


class MessageHandler:
    def __init__(self, client):
        self.client = client

    def send_message(
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

    def decode_message(self, target, text, iv, key=None):
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

    def like_message(self, message_id):
        return self.client._post("message/like", data={"message_id": message_id})

    def unlike_message(self, message_id):
        return self.client._post("message/unlike", data={"message_id": message_id})

    def delete_message(self, message_id):
        return self.client._post("message/delete", data={"message_id": message_id})

    def get_messages(self, conversation_id, limit: int = 30, offset: int = 0):
        target_type = self.client.tools.get_type(conversation_id)

        data = {
            f"{target_type}_id": id,
            "source": target_type,
            "limit": limit,
            "offset": offset,
        }

        response = self.client._post("message/content", data=data)
        response = response["messages"]
        conversation_key = self.client.get_conversation_key(id, target_type)

        messages = []

        for message in response:
            if message["kind"] != "message":
                continue
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
                    "text": self.client.messages.decode_message(
                        target=message[f"{target_type}_id"],
                        text=message["text"],
                        iv=message["iv"],
                    ),
                    "time": message["time"],
                    "location": {"longitude": longitude, "latitude": latitude},
                    "likes": message["likes"],
                    "files": [
                        {
                            "id": file["id"],
                            "times_downloaded": file["times_downloaded"],
                            "size_byte": file["size_byte"],
                        }
                        for file in message["files"]
                    ],
                }
            )
        return messages


class Message:
    def __init__(self, client, data):
        self.client = client
        self.id = data["id"]
        self.content_encrypted = data["text"]
        self.encrypted = data["encrypted"]
        self.type = "conversation" if data["channel_id"] == 0 else "channel"
        self.iv = data["iv"] if self.encrypted else None
        self.content = (
            self.client.messages.decode_message(
                data[f"{self.type}_id"], self.encrypted, self.iv
            )
            if self.encrypted
            else self.content_encrypted
        )
        self.author = User(self.client, data["sender"])

    def like(self):
        return self.client.messages.like_message(self.id)

    def unlike(self):
        return self.client.messages.unlike_message(self.id)

    def delete(self):
        return self.client.messages.delete_message(self.id)
