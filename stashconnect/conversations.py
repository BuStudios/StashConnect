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

from .models import Conversation


class ConversationManager:
    def __init__(self, client):
        self.client = client

    def archive(self, conversation_id: str | int) -> dict:
        """Archives a conversation

        Args:
            conversation_id (str | int): The conversations id.

        Returns:
            dict: The success status.
        """
        response = self.client._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response

    def favorite(self, conversation_id: str | int) -> dict:
        """Favorites a conversation

        Args:
            conversation_id (str | int): The conversations id.

        Returns:
            dict: The success status.
        """
        response = self.client._post(
            "message/set_favorite",
            data={"conversation_id": conversation_id, "favorite": True},
        )
        return response

    def unfavorite(self, conversation_id: str | int) -> dict:
        """Unfavorites a conversation

        Args:
            conversation_id (str | int): The conversations id.

        Returns:
            dict: The success status.
        """
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

    def create(self, members: str | int | list) -> Conversation:
        """Creates a conversation with users

        Args:
            members (str | int | list): The members of the conversation.

        Returns:
            Conversation: A conversation object.
        """
        conversation_key = Crypto.Random.get_random_bytes(32)
        users = []

        # encrypt conversation key using private key
        encryptor = Crypto.Cipher.PKCS1_OAEP.new(self.client._private_key.publickey())
        encrypted_key = encryptor.encrypt(conversation_key)

        # i dont know where the private signing key is located
        # if you know where it is please tell me :)

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
            user = self.client.users._info(member)

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

    def info(self, conversation_id: str | int) -> Conversation:
        """Fetches the info of a conversation

        Args:
            conversation_id (str | int): The conversations info.

        Returns:
            Conversation: A conversation object.
        """
        response = self.client._post(
            "message/conversation", data={"conversation_id": conversation_id}
        )
        return Conversation(self.client, response["conversation"])
