import Crypto
import Crypto.Cipher
import Crypto.Cipher.PKCS1_OAEP
import Crypto.Hash
import Crypto.Hash.SHA256
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto.Random
import Crypto.SelfTest
import Crypto.Signature
import Crypto.Signature.pkcs1_15
import Crypto.Util

import base64
import json
import time

from .users import User


class ConversationManager:
    def __init__(self, client):
        self.client = client

    def archive(self, conversation_id):
        response = self.client._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response

    def favorite(self, conversation_id):
        response = self.client._post(
            "message/set_favorite",
            data={"conversation_id": conversation_id, "favorite": True},
        )
        return response

    def unfavorite(self, conversation_id):
        response = self.client._post(
            "message/set_favorite",
            data={"conversation_id": conversation_id, "favorite": False},
        )
        return response

    def disable_notifications(
        self, conversation_id: int | str, duration: int | str
    ) -> str:
        """Disables notifications for a conversation

        Args:
            conversation_id (int | str): The conversations id.
            duration (int | str): how long the block should last (seconds).

        Returns:
            str: The end timestamp.
        """
        return self.client._post(
            "push/disable_notifications",
            data={
                "type": "conversation",
                "content_id": conversation_id,
                "duration": duration,
            },
        )

    def enable_notifications(self, conversation_id: int | str) -> dict:
        """Enables notifications for a conversation

        Args:
            conversation_id (int | str): The conversations id.

        Returns:
            dict: The success status.
        """
        return self.client._post(
            "push/enable_notifications",
            data={"type": "conversation", "content_id": conversation_id},
        )

    def create(self, members):
        conversation_key = Crypto.Random.get_random_bytes(32)
        users = []

        # encrypt conversation key using private key
        encryptor = Crypto.Cipher.PKCS1_OAEP.new(self.client._private_key.publickey())
        encrypted_key = encryptor.encrypt(conversation_key)

        # i dont know where the private signing key is located
        # if anybody knows where it is please tell me :)

        # hash = Crypto.Hash.SHA256.new(encrypted_key)
        # signature = Crypto.Signature.pkcs1_15.new(self.client._private_key).sign(hash)
        # encoded_signature = base64.b64encode(signature).decode("utf-8")

        users.append(
            {
                "id": int(self.client.user_id),
                "key": base64.b64encode(encrypted_key).decode("utf-8"),
                # "signature": encoded_signature,
                # "userVerified": True,
            }
        )

        if isinstance(members, str | int):
            members = [members]

        # encrypt conversation key using public key for all members
        for member in members:
            user = self.client.users.info(member)

            publickey = Crypto.PublicKey.RSA.import_key(user["public_key"])

            encryptor = Crypto.Cipher.PKCS1_OAEP.new(publickey)
            encrypted_key = encryptor.encrypt(conversation_key)

            # hash = Crypto.Hash.SHA256.new(encrypted_key)
            # signature = Crypto.Signature.pkcs1_15.new(self.client._private_key).sign(hash)
            # encoded_signature = base64.b64encode(signature).decode("utf-8")

            users.append(
                {
                    "id": int(user["id"]),
                    "key": base64.b64encode(encrypted_key).decode("utf-8"),
                    # "signature": encoded_signature,
                    # "expiry": int(round(time.time())),
                    # "userVerified": True,
                }
            )

        response = self.client._post(
            "message/createEncryptedConversation",
            data={"members": json.dumps(users), "unique_identifier": conversation_key},
        )

        return Conversation(self.client, response["conversation"])

    def get(self, conversation_id):
        response = self.client._post(
            "message/conversation", data={"conversation_id": conversation_id}
        )
        return Conversation(self.client, response["conversation"])


class Conversation:
    def __init__(self, client, data):
        self.client = client
        self.id = data["id"]

        self.type = "conversation"
        self.type_id = data["id"]

        self.conversation_id = data["id"]
        self.channel_id = data["id"]

        self.key_sender = data["key_sender"]
        self.conversation_key = self.client.get_conversation_key(
            data["id"], self.type, key=data["key"]
        )

        self.encrypted = data["encrypted"]
        self.favorited = data["favorite"]
        self.archived = data["archive"]

        self.last_action = data["last_action"]
        self.last_activity = data["last_activity"]

        self.muted = data["muted"]
        self.name = data["name"]

        self.unread_messages = data["unread_messages"]
        self.user_count = data["user_count"]

        self.members = [User(self.client, member) for member in data["members"]]
        self.callable = [User(self.client, member) for member in data["callable"]]

    def archive(self):
        return self.client.conversations.archive(self.id)

    def favorite(self):
        return self.client.conversations.favorite(self.id)

    def unfavorite(self):
        return self.client.conversations.unfavorite(self.id)

    def disable_notifications(self, duration: int | str) -> str:
        return self.client.conversations.disable_notifications(self.id, duration)

    def enable_notifications(self) -> dict:
        return self.client.conversations.enable_notifications(self.id)
