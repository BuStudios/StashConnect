import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto.Random
import Crypto

import base64
import json

from .models import User
from typing import Generator


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

    def edit(
        self,
        company_id,
        channel_id,
        *,
        description="",
        channel_name,
        password=None,
        visible=True,
        writable="all",
        inviteable="all",
        show_activities=True,
        show_membership_activities=True
    ):

        data = {
            "channel_id": channel_id,
            "company_id": company_id,
            "channel_name": channel_name,
            "description": description,
            "writable": writable,
            "visible": visible,
            "inviteable": inviteable,
            "password": password,
            "password_repeat": password,
            "show_activities": show_activities,
            "show_membership_activities": show_membership_activities,
        }

        response = self.client._post("channels/edit", data=data)
        return response["channel"]

    def quit(self, channel_id):
        response = self.client._post("channels/quit", data={"channel_id": channel_id})
        return response

    def rename(self, channel_id, channel_name):
        response = self.client._post(
            "channels/rename",
            data={"channel_id": channel_id, "channel_name": channel_name},
        )
        return response

    def edit_description(self, channel_id, description):
        response = self.client._post(
            "channels/editDescription",
            data={"channel_id": channel_id, "description": description},
        )
        return response

    def delete(self, channel_id):
        response = self.client._post("channels/delete", data={"channel_id": channel_id})
        return response

    def change_permission(self, channel_id, writable):
        response = self.client._post(
            "channels/changePermissions",
            data={"channel_id": channel_id, "writable": writable},
        )
        return response["channel"]

    def remove_user(self, channel_id, user_id):
        response = self.client._post(
            "channels/removeUser", data={"channel_id": channel_id, "user_id": user_id}
        )
        return response["channel"]

    def add_manager_status(self, channel_id, user_id):
        response = self.client._post(
            "channels/addModeratorStatus",
            data={"channel_id": channel_id, "user_id": user_id},
        )
        return response["channel"]

    def remove_manager_status(self, channel_id, user_id):
        response = self.client._post(
            "channels/removeModeratorStatus",
            data={"channel_id": channel_id, "user_id": user_id},
        )
        return response["channel"]

    def edit_password(self, channel_id, password):
        response = self.client._post(
            "channels/editPassword",
            data={"password": password, "channel_id": channel_id},
        )
        return response

    def info(self, channel_id: int | str, without_members: bool = True):
        response = self.client._post(
            "channels/info",
            data={"channel_id": channel_id, "without_members": without_members},
        )
        return response["channels"]

    def invite(
        self,
        channel_id: int | str,
        members: int | str | list | tuple,
        text: str = "",
        expiry: int | str = None,
    ) -> dict:
        """Created an invite for a channel

        Args:
            channel_id (int | str): The id of the channel.
            members (int | str | list | tuple): Members to invite as a list or string.
            text (str, optional): The text invited users will become. Defaults to "".
            expiry (int | str, optional): Expiry time as a unix timestamp. Defaults to None.

        Returns:
            dict: The success status.
        """
        # fetch the channels key
        conversation_key = self.client.get_conversation_key(channel_id, "channel")
        users = []

        if isinstance(members, str | int):
            members = [members]

        for member in members:
            user = self.client.users._info(member)

            publickey = Crypto.PublicKey.RSA.import_key(user["public_key"])
            encryptor = Crypto.Cipher.PKCS1_OAEP.new(publickey)
            encrypted_key = encryptor.encrypt(conversation_key)

            users.append(
                {
                    "id": int(user["id"]),
                    "key": base64.b64encode(encrypted_key).decode("utf-8"),
                    "expiry": expiry,
                    "userVerified": True,
                }
            )

        response = self.client._post(
            "channels/createInvite",
            data={
                "channel_id": int(channel_id),
                "users": json.dumps(users),
                "text": text,
            },
        )

        return response

    def members(
        self,
        channel_id: int | str,
        *,
        search: str | int = None,
        limit: int | str = 40,
        offset: int | str = 0
    ) -> Generator[User, None, None]:
        """Lists the members if a channel as a generator

        Args:
            channel_id (int | str): The channels id.
            search (str | int, optional): The search keyword that is used. Defaults to None.
            limit (int | str, optional): Limit of answer. Defaults to 40.
            offset (int | str, optional): Offset of answer. Defaults to 0.

        Yields:
            Generator[User, None, None]: A generator object with a User object
            (use: for member in members).
        """
        data = {
            "channel_id": channel_id,
            "limit": limit,
            "offset": offset,
            "filter": "members",
            "sorting": ["first_name_asc", "last_name_asc"],
            "search": search,
        }

        response = self.client._post("channels/members", data=data)

        for member in response["members"]:
            yield User(self.client, member)

    def join(self, channel_id: int | str, *, password: str | int = ""):
        response = self.client._post(
            "channels/join", data={"channel_id": channel_id, "password": password}
        )
        return response["channel"]

    def recommendations(self, company_id: int | str):
        response = self.client._post(
            "channels/recommendations", data={"company": company_id}
        )
        return response["channels"]

    def visible(
        self,
        company_id: int | str,
        *,
        limit: int | str = 30,
        offset: int | str = 0,
        search: str | int = ""
    ):
        response = self.client._post(
            "channels/visible",
            data={
                "company": company_id,
                "limit": limit,
                "offset": offset,
                "search": search,
            },
        )
        return response["channels"]

    def joined(self, company_id: int | str):
        response = self.client._post(
            "channels/subscripted", data={"company": company_id}
        )
        return response["channels"]

    def accept_invite(self, invite_id: int | str) -> dict:
        """Accepts an invite.

        Args:
            invite_id (int | str): The id of the invite.

        Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/acceptInvite", data={"invite_id": invite_id}
        )
        return response

    def decline_invite(self, invite_id: int | str) -> dict:
        """Declines an invite.

        Args:
            invite_id (int | str): The id of the invite.

        Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/declineInvite", data={"invite_id": invite_id}
        )
        return response
