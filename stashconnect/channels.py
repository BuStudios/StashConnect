import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.Random
import Crypto

import base64


class ChannelManager:
    def __init__(self, client):
        self.client = client

    def create(
        self,
        channel_name,
        company_id,
        *,
        description="",
        password=None,
        channel_type="encrypted",
        visible=True,
        writable="all",
        inviteable="all",
        show_activities=True,
        show_membership_activities=True
    ):
        conversation_key = Crypto.Random.get_random_bytes(32)
        encryptor = Crypto.Cipher.PKCS1_OAEP.new(self.client._private_key.publickey())

        encrypted_key = encryptor.encrypt(conversation_key)

        data = {
            "channel_name": channel_name,
            "company": company_id,
            "password": password,
            "password_repeat": password,
            "description": description,
            "type": channel_type,
            "visible": visible,
            "writable": writable,
            "encryption_key": base64.b64encode(encrypted_key).decode("utf-8"),
            "inviteable": inviteable,
            "show_activities": show_activities,
            "show_membership_activities": show_membership_activities,
        }

        response = self.client._post("channels/create", data=data)
        return response["channel"]
