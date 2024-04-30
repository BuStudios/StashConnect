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


class Conversations:
    def __init__(self, client):
        self.client = client

    def archive_conversation(self, conversation_id):
        response = self.client._post(
            "message/archiveConversation", data={"conversation_id": conversation_id}
        )
        return response

    def create_conversation(self, members):
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

        return response["conversation"]
