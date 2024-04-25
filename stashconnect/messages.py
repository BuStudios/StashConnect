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


class Message:

    def send_message(self, target, text, files, location, **kwargs):

        iv = Crypto.Random.get_random_bytes(16)
        conversation_key = self.get_conversation_key(target, "conversation")

        text_bytes = text.encode("utf-8")
        text = CryptoUtils.encrypt_aes(text_bytes, conversation_key, iv)

        files_sent = []

        if files is not None:

            if isinstance(files, str):
                files = [files]

            for file in files:
                file = self.upload_file(target, file)
                files_sent.append(int(file["id"]))

        data = {
            "target": "conversation",
            "conversation_id": target,
            "text": text.hex(),
            "files": json.dumps(files_sent),
            "url": [],
            "encrypted": True,
            "iv": iv.hex(),
            "verification": "",
            "type": "text",
            "is_forwarded": False,
        }

        data.update(kwargs)

        if location is True:

            location = self.get_location()["location"]

            data["latitude"] = CryptoUtils.encrypt_aes(
                str(location["latitude"]).encode("utf-8"), conversation_key, iv=iv
            ).hex()
            data["longitude"] = CryptoUtils.encrypt_aes(
                str(location["longitude"]).encode("utf-8"), conversation_key, iv=iv
            ).hex()

        elif isinstance(location, tuple | list):

            data["latitude"] = CryptoUtils.encrypt_aes(
                str(location[0]).encode("utf-8"), conversation_key, iv=iv
            ).hex()

            data["longitude"] = CryptoUtils.encrypt_aes(
                str(location[1]).encode("utf-8"), conversation_key, iv=iv
            ).hex()

        response = self._post("message/send", data=data)
        return response

    def decode_message(self, target, text, iv, key):
        target_type = self.get_type(target)

        if text == "":
            return text
        else:
            try:
                if self._private_key is None:
                    return text
                else:
                    conversation_key = self.get_conversation_key(
                        target, target_type, key=key
                    )

                    text = CryptoUtils.decrypt_aes(
                        bytes.fromhex(text), conversation_key, bytes.fromhex(iv)
                    )
                    return text.decode("utf-8")
            except Exception:
                return text

    def like_message(self, id):
        return self._post("message/like", data={"message_id": id})

    def get_messages(self, id, limit, offset):
        target_type = self.get_type(id)

        data = {
            f"{target_type}_id": id,
            "source": target_type,
            "limit": limit,
            "offset": offset,
        }

        response = self._post("message/content", data=data)
        response = response["messages"]
        conversation_key = self.get_conversation_key(id, target_type)

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
                    "text": self.decode_message(
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
