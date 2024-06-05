import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto.Random
import Crypto

import base64
import json

from .models import User, Channel
from typing import Generator


class ChannelManager:
    def __init__(self, client):
        self.client = client

    def create(
        self,
        channel_name: str,
        company_id: int | str,
        *,
        description: str = "",
        password: str = None,
        channel_type: str = "encrypted",
        visible: bool = True,
        writable: str = "all",
        inviteable: str = "all",
        show_activities: bool = True,
        show_membership_activities: bool = True
    ) -> Channel:
        """## Creates a channel.

        #### Args:
            channel_name (str): The channels name.
            company_id (int | str): The companies id.
            description (str, optional): The channels description. Defaults to "".
            password (str, optional): The channels password. Defaults to None.
            channel_type (str, optional): The channels type. Defaults to "encrypted".
            visible (bool, optional): The channels visibility. Defaults to True.
            writable (str, optional): Sets who can write in the channel. Defaults to "all".
            inviteable (str, optional): Sets who can invite other users. Defaults to "all".
            show_activities (bool, optional): [name]. Defaults to True.
            show_membership_activities (bool, optional): [name]. Defaults to True.

        #### Returns:
            Channel: A channel object.
        """
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
        return Channel(self.client, response["channel"])

    def edit(
        self,
        company_id: int | str,
        channel_id: int | str,
        *,
        description: str = "",
        channel_name: str,
        password: str = None,
        visible: bool = True,
        writable: str = "all",
        inviteable: str = "all",
        show_activities: bool = True,
        show_membership_activities: bool = True
    ) -> Channel:
        """## Edits a channel.

        #### Args:
            company_id (int | str): The companies id.
            channel_id (int | str): The channels id.
            channel_name (str): The channels name.
            description (str, optional): The channels description. Defaults to "".
            password (str, optional): The channels password. Defaults to None.
            visible (bool, optional): The channels visibility. Defaults to True.
            writable (str, optional): Sets who can write in the channel. Defaults to "all".
            inviteable (str, optional): Sets who can invite other users. Defaults to "all".
            show_activities (bool, optional): [name]. Defaults to True.
            show_membership_activities (bool, optional): [name]. Defaults to True.

        #### Returns:
            Channel: A channel object.
        """

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
        return Channel(self.client, response["channel"])

    def quit(self, channel_id: int | str) -> dict:
        """## Leaves a channel.

        #### Args:
            channel_id (int | str): The channels id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post("channels/quit", data={"channel_id": channel_id})
        return response

    def rename(self, channel_id: int | str, channel_name: str) -> dict:
        """## Renames a channel.

        #### Args:
            channel_id (int | str): The channels id.
            channel_name (str): The new channel name.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/rename",
            data={"channel_id": channel_id, "channel_name": channel_name},
        )
        return response

    def edit_description(self, channel_id: int | str, description: str) -> dict:
        """## Edits the description of a channel.

        #### Args:
            channel_id (int | str): The channels id.
            description (str): The new channel description.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/editDescription",
            data={"channel_id": channel_id, "description": description},
        )
        return response

    def delete(self, channel_id: int | str) -> dict:
        """## Deletes a channel (without confirmation!).

        #### Args:
            channel_id (int | str): The channels id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post("channels/delete", data={"channel_id": channel_id})
        return response

    def change_permission(self, channel_id: int | str, writable: str) -> Channel:
        """## Sets who can write in the channel.

        #### Args:
            channel_id (int | str): The channels id.
            writable (str): Sets who can write in the channel.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/changePermissions",
            data={"channel_id": channel_id, "writable": writable},
        )
        return Channel(self.client, response["channel"])

    def remove_user(self, channel_id: int | str, user_id: int | str) -> Channel:
        """## Removes the user from the channel.

        #### Args:
            channel_id (int | str): The channels id.
            user_id (int | str): The users id.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/removeUser", data={"channel_id": channel_id, "user_id": user_id}
        )
        return Channel(self.client, response["channel"])

    def add_manager_status(self, channel_id: int | str, user_id: int | str) -> Channel:
        """## Adds a moderation status.

        #### Args:
            channel_id (int | str): The channels id.
            user_id (int | str): The users id.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/addModeratorStatus",
            data={"channel_id": channel_id, "user_id": user_id},
        )
        return Channel(self.client, response["channel"])

    def remove_manager_status(
        self, channel_id: int | str, user_id: int | str
    ) -> Channel:
        """## Removes a moderation status.

        #### Args:
            channel_id (int | str): The channels id.
            user_id (int | str): The users id.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/removeModeratorStatus",
            data={"channel_id": channel_id, "user_id": user_id},
        )
        return Channel(self.client, response["channel"])

    def edit_password(self, channel_id: int | str, password: str) -> dict:
        """## Edits the password of the channel.

        #### Args:
            channel_id (int | str): The channels id.
            password (str): The new password.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/editPassword",
            data={"password": password, "channel_id": channel_id},
        )
        return response

    def _info(self, channel_id: int | str, without_members: bool = True) -> dict:
        """## Gets the info of a channel (dict).

        #### Args:
            channel_id (int | str): The channels id.
            without_members (bool, optional): Returns the members. Defaults to True.

        #### Returns:
            dict: The channel info as a dict.
        """
        response = self.client._post(
            "channels/info",
            data={"channel_id": channel_id, "without_members": without_members},
        )
        return response["channels"]

    def info(self, channel_id: int | str, without_members: bool = True) -> Channel:
        """## Gets the info of a channel.

        #### Args:
            channel_id (int | str): The channels id.
            without_members (bool, optional): Returns the members. Defaults to True.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/info",
            data={"channel_id": channel_id, "without_members": without_members},
        )
        return Channel(self.client, response["channels"])

    def invite(
        self,
        channel_id: int | str,
        members: int | str | list | tuple,
        text: str = "",
        expiry: int | str = None,
    ) -> dict:
        """## Creates an invite for a channel.

        #### Args:
            channel_id (int | str): The id of the channel.
            members (int | str | list | tuple): Members to invite as a list or string.
            text (str, optional): The text invited users will become. Defaults to "".
            expiry (int | str, optional): Expiry time as a unix timestamp. Defaults to None.

        #### Returns:
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
        """## Lists the members if a channel as a generator.

        #### Args:
            channel_id (int | str): The channels id.
            search (str | int, optional): The search keyword that is used. Defaults to None.
            limit (int | str, optional): Limit of answer. Defaults to 40.
            offset (int | str, optional): Offset of answer. Defaults to 0.

        #### Yields:
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

    def join(self, channel_id: int | str, *, password: str | int = "") -> Channel:
        """## Joins a channel.

        #### Args:
            channel_id (int | str): The channels id.
            password (str | int, optional): The password. Defaults to "".

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/join", data={"channel_id": channel_id, "password": password}
        )
        return Channel(self.client, response["channel"])

    def recommendations(self, company_id: int | str) -> Channel:
        """## Gets custom channel recommendations.

        #### Args:
            company_id (int | str): The companies id.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/recommendations", data={"company": company_id}
        )
        return Channel(self.client, response["channels"])

    def visible(
        self,
        company_id: int | str,
        *,
        limit: int | str = 30,
        offset: int | str = 0,
        search: str | int = ""
    ) -> Channel:
        """## Gets all visible channels.

        #### Args:
            company_id (int | str): The companies id.
            limit (int | str, optional): The returned limit. Defaults to 30.
            offset (int | str, optional): The returned offset. Defaults to 0.
            search (str | int, optional): The search keyword. Defaults to "".

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/visible",
            data={
                "company": company_id,
                "limit": limit,
                "offset": offset,
                "search": search,
            },
        )
        return Channel(self.client, response["channels"])

    def joined(self, company_id: int | str) -> Channel:
        """## Gets all joined channels.

        #### Args:
            company_id (int | str): The companies id.

        #### Returns:
            Channel: A channel object.
        """
        response = self.client._post(
            "channels/subscripted", data={"company": company_id}
        )
        return Channel(self.client, response["channels"])

    def accept_invite(self, invite_id: int | str) -> dict:
        """## Accepts an invite.

        #### Args:
            invite_id (int | str): The id of the invite.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/acceptInvite", data={"invite_id": invite_id}
        )
        return response

    def decline_invite(self, invite_id: int | str) -> dict:
        """## Declines an invite.

        #### Args:
            invite_id (int | str): The id of the invite.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "channels/declineInvite", data={"invite_id": invite_id}
        )
        return response

    def favorite(self, channel_id: int | str) -> dict:
        """## Favorites a channel.

        #### Args:
            channel_id (int | str): The channels id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "message/set_favorite",
            data={"channel_id": channel_id, "favorite": True},
        )
        return response

    def unfavorite(self, channel_id: int | str) -> dict:
        """## Unfavorites a channel.

        #### Args:
            channel_id (int | str): The channels id.

        #### Returns:
            dict: The success status.
        """
        response = self.client._post(
            "message/set_favorite",
            data={"channel_id": channel_id, "favorite": False},
        )
        return response

    def disable_notifications(self, channel_id: int | str, duration: int | str) -> dict:
        """## Disables notifications for a channel.

        #### Args:
            channel_id (int | str): The channels id.
            duration (int | str): how long the block should last (seconds).

        #### Returns:
            dict: The end timestamp.
        """
        return self.client._post(
            "push/disable_notifications",
            data={
                "type": "channel",
                "content_id": channel_id,
                "duration": duration,
            },
        )

    def enable_notifications(self, channel_id: int | str) -> dict:
        """## Enables notifications for a channel.

        #### Args:
            channel_id (int | str): The channels id.

        #### Returns:
            dict: The success status.
        """
        return self.client._post(
            "push/enable_notifications",
            data={"type": "channel", "content_id": channel_id},
        )
