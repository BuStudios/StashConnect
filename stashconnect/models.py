# All returnable objects are stored here

from .crypto_utils import CryptoUtils


class Message:
    def __init__(self, client, data):
        self.client = client
        self.id = data["id"]

        if data["channel_id"] == 0:
            self.type = "conversation"
            self.type_id = data["conversation_id"]
        else:
            self.type = "channel"
            self.type_id = data["channel_id"]

        self.conversation_key = self.client.get_conversation_key(
            data[f"{self.type}_id"], self.type
        )

        self.content_encrypted = data["text"]
        self.encrypted = data["encrypted"]
        self.iv = data["iv"] if self.encrypted else None

        if self.encrypted:
            self.content = self.client.messages.decode(
                data[f"{self.type}_id"], self.content_encrypted, self.iv
            )
        else:
            self.content = self.content_encrypted

        self.timestamp = data["time"]
        self.channel_id = data["channel_id"]
        self.conversation_id = data["conversation_id"]

        self.files = data["files"]
        self.flagged = data["flagged"]

        self.liked = data["liked"]
        self.likes = data["likes"]
        self.links = data["links"]

        self._decrypt_location(data["location"])

        self.author = User(self.client, data["sender"])

    def _decrypt_location(self, location):

        if location["encrypted"]:

            if self.client._private_key is None:
                print(
                    "Could not decrypt encrypted location as no encryption password was provided"
                )
                self.longitude = location["longitude"]
                self.latitude = location["latitude"]

            self.longitude = CryptoUtils.decrypt_aes(
                bytes.fromhex(location["longitude"]),
                self.conversation_key,
                bytes.fromhex(self.iv),
            ).decode("utf-8")

            self.latitude = CryptoUtils.decrypt_aes(
                bytes.fromhex(location["latitude"]),
                self.conversation_key,
                bytes.fromhex(self.iv),
            ).decode("utf-8")
        else:
            self.longitude = location["longitude"]
            self.latitude = location["latitude"]

    def like(self):
        return self.client.messages.like(self.id)

    def unlike(self):
        return self.client.messages.unlike(self.id)

    def delete(self):
        return self.client.messages.delete(self.id)

    def flag(self):
        return self.client.messages.flag(self.id)

    def unflag(self):
        return self.client.messages.unflag(self.id)

    def respond(
        self,
        text: str,
        *,
        files=None,
        url="",
        location: bool | tuple | list = None,
        encrypted: bool = True,
        **kwargs,
    ):
        return self.client.messages.send(
            target=self.type_id,
            text=text,
            files=files,
            url=url,
            location=location,
            encrypted=encrypted,
            **kwargs,
        )


class User:
    def __init__(self, client, data) -> None:
        self.client = client
        self.id = data["id"]

        try:
            self.set_attributes(data)
        except KeyError:
            user_data = self.client.users._info(self.id)
            self.set_attributes(user_data)

    def set_attributes(self, data):
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]

        self.email = data["email"]
        self.status = data["status"]
        self.image = data["image"]

        self.language = data["language"]
        self.last_login = data["last_login"]
        self.online = data["online"]
        self.permissions = data["permissions"]

        self.public_key = data["public_key"]
        self.companies = data["roles"]


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


class Company:
    def __init__(self, client, data):
        self.client = client

        if "company_id" in data:
            data = self.client._post(
                "company/details", data={"company_id": data["company_id"]}
            )["company"]

        self.id = data["id"]

        self.name = data["name"]
        self.manager = User(self.client, data["manager"])

        self.time_created = data["created"]
        self.time_joined = data["time_joined"]
        self.unread_messages = data["unread_messages"]

        self.logo_url = data["logo_url"]
        self.domain = data["domain"]

        self.max_users = data["max_users"]
        self.active_users = data["users"]["active"]
        self.created_users = data["users"]["created"]

        self.membership_expiry = data["membership_expiry"]
        self.online_payment = data["online_payment"]
        self.protected = data["protected"]

        self.provider = data["provider"]
        self.quota = data["quota"]
        self.freemium = data["freemium"]

        self.deactivated = data["deactivated"]
        self.deleted = data["deleted"]
        self.features = data["features"]

        self.permission = data["permission"]
        self.roles = data["roles"]
        self.settings = data["settings"]


class Channel:
    def __init__(self, client, data):
        self.client = client
        self.id = data["id"]

        try:
            self.set_attributes(data)
        except KeyError:
            data = self.client.channels.info(self.id)
            self.set_attributes(data)

    def set_attributes(self, data):
        self.company = Company(self.client, {"company_id": data["company"]})

        self.crypto_properties = data["crypto_properties"]
        self.encrypted = data["encrypted"]
        self.federated = data["federated"]
        self.unique_identifier = data["unique_identifier"]

        self.description = data["description"]
        self.name = data["name"]
        self.image = data["image"]
        self.group_id = data["group_id"]

        self.can_leave = data["can_leave"]
        self.inviteable = data["inviteable"]
        self.last_action = data["last_action"]

        self.ldap_name = data["ldap_name"]
        self.mx_room_alias = data["mx_room_alias"]
        self.mx_room_id = data["mx_room_id"]
        self.mx_room_server_status = data["mx_room_server_status"]

        self.num_members_without_keys = data["num_members_without_keys"]
        self.password = data["password"]
        self.pending_count = data["pending_count"]
        self.request_count = data["request_count"]

        self.show_activities = data["show_activities"]
        self.show_membership_activities = data["show_membership_activities"]
        self.type = data["type"]

        self.user_count = data["user_count"]
        self.visible = data["visible"]
        self.writable = data["writable"]

        self.is_member = data["membership"]["is_member"]
        self.joined = data["membership"]["joined"]
        self.may_manage = data["membership"]["may_manage"]
        self.muted = data["membership"]["muted"]
        self.write = data["membership"]["write"]

        self.confirmation = data["membership"]["confirmation"]
        self.invited_at = data["membership"]["invited_at"]
        self.invited_by = data["membership"]["invited_by"]
        self.invited_by_mx_user_id = data["membership"]["invited_by_mx_user_id"]
