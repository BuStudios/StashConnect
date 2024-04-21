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

import requests
import json
import base64
import time

from PIL import Image
import io

import socketio

from .messages import Message
from .settings import Settings
from .users import Users
from .crypto_utils import CryptoUtils
from .conversations import Conversations

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en",
    "Cache-Control": "no-cache",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://app.schul.cloud/",
}


class Client:
    """Represents a client connection to Stashcat API.

    Atrributes:
        .email (str): The user's email used for authentication.
        .password (str): The user's password.
        .device_id (str): The device_id used to login, defaults to "stashconnect123".
        .client_key (str): The key used in submitting requests.
        .socket_id (str): The ID for the websocket connection.
        .user_id (str): The unique ID of the connected user's account.
        .image_url (str): URL to the user's profile image.
        .first_name (str): User's first name.
        .last_name (str): User's last name.

    Methods:
        .send_message(target, text). Encrypts and sends a message to a specific conversation.
        .decode_message(text, target, iv, key -> optional): Decrypts an encrypted message.
        .change_profile_picture(url): Updates the user's profile image with an image URL.
        .change_status(status): Updates the user's status.
    """

    def __init__(self, *, email, password, device_id=None, encryption_password=None):

        self.email = email
        self.password = password

        self.device_id = "stashconnect123" if device_id is None else device_id
        self.app_name = "stashconnect:alpha"

        self._main_url = "https://api.stashcat.com/"
        self._push_url = "https://push.stashcat.com/"

        self._headers = headers
        self._session = requests.Session()
        self._session.headers.update(self._headers)

        self._login()

        self.conversation_keys = {}
        self.events = {}

        self._private_key = None
        self._ping_target = None

        if encryption_password is not None:
            self.get_private_key(encryption_password=encryption_password)

    def _login(self):

        data = {
            "email": self.email,
            "password": self.password,
            "app_name": self.app_name,
            "encrypted": "true",
            "callable": "true",
        }

        response = self._post("auth/login", data=data, auth=False)

        self.client_key = response["client_key"]
        self.socket_id = response["userinfo"]["socket_id"]
        self.user_id = response["userinfo"]["id"]
        self.image_url = response["userinfo"]["image"]

        self.first_name = response["userinfo"]["first_name"]
        self.last_name = response["userinfo"]["last_name"]

        print(f"Logged in as {self.first_name} {self.last_name}!")

        return response

    def _post(self, url, *, data, auth=True, **kwargs):

        data["device_id"] = self.device_id

        if auth is True:
            data["client_key"] = self.client_key

        response = self._session.post(f"{self._main_url}{url}", data=data, **kwargs)

        response.raise_for_status()

        response = response.json()
        status = response["status"]
        payload = response["payload"]

        if status["value"] != "OK":
            # create custom exceptions
            raise Exception(status["message"])

        return payload

    def verify_login(self):

        data = {"app_name": self.app_name, "encrypted": True, "callable": True}

        response = self._post("/auth/check", data=data)
        return response

    def get_private_key(self, *, encryption_password: str) -> None:
        
        print("Importing private key. Please wait...")
        response = self._post("security/get_private_key", data={})
        encrypted_key = json.loads(response["keys"]["private_key"])

        self._private_key = CryptoUtils.load_private_key(encrypted_key["private"], encryption_password)

    def get_conversation_key(self, target, key=None):

        try:
            return self.conversation_keys[target]
        except KeyError:
            encrypted_key = key

            if encrypted_key is None:

                response = self._post(
                    "message/conversation", data={"conversation_id": target}
                )
                encrypted_key = response["conversation"]["key"]

            decrypted_key = CryptoUtils.decrypt_key(encrypted_key, self._private_key)

            self.conversation_keys[target] = decrypted_key
            return self.conversation_keys[target]

    # MESSAGES
    def send_message(self, target, text: str, location: bool | tuple | list = None):
        return Message.send_message(self, target, text, location=location)

    def decode_message(self, *, target, text, iv, key=None):
        return Message.decode_message(self, target=target, text=text, iv=iv, key=key)

    # USERS
    def get_location(self):
        return Users.get_location(self)

    def change_status(self, status: str):
        return Users.change_status(self, status)

    def change_profile_picture(self, *, url: str):
        return Users.change_profile_picture(self, url=url)

    def reset_profile_picture(self):
        return Users.reset_profile_picture(self)

    # CONVERSATIONS
    def archive_conversation(self, conversation_id):
        return Conversations.archive_conversation(self, conversation_id)

    def get_messages(self, conversation_id, limit: int = 30, offset: int = 0):
        return Conversations.get_messages(
            self, conversation_id, limit=limit, offset=offset
        )
        
    def upload_file(self, target, filepath):
        return Conversations.upload_file(self, target, filepath)

    # SETTINGS
    def get_notification_count(self) -> int:
        return Settings.get_notification_count(self)

    def get_notifications(self, limit: int = 20, offset: int = 0) -> dict:
        return Settings.get_notifications(self, limit, offset)

    def change_email(self, email: str):
        return Settings.change_email(self, email)

    def resend_verification_email(self, email: str):
        return Settings.resend_verification_email(self, email)

    def change_password(self, new_password: str, old_password: str):
        return Settings.change_password(self, new_password, old_password)

    def get_settings(self):
        return Settings.get_settings(self)

    def get_me(self):
        return Settings.get_me(self)

    def get_active_devices(self):
        return Settings.get_active_devices(self)

    def event(self, name):

        def decorator(func):
            self.events[name] = func
            return func

        return decorator

    def _run(self, debug=False):

        self.sio = socketio.Client(logger=debug, engineio_logger=debug)

        @self.sio.event
        def connect():

            print("Connected to the server.")

            data = {
                "hidden_id": self.socket_id,
                "device_id": self.device_id,
                "client_key": self.client_key,
            }

            self.sio.emit("userid", data)

        @self.sio.event
        def disconnect():
            print("Disconnected from the server")
            self.sio.disconnect()

        @self.sio.on("user-started-typing")
        def pong(*args):
            if str(args[2]) == str(self.user_id) and str(args[1]) == str(
                self._ping_target
            ):
                self._end_time = time.perf_counter()

        for event_name, event_handler in self.events.items():
            self.sio.on(event_name)(event_handler)

        self.sio.connect(self._push_url)
        self.sio.wait()

    def run(self, debug=False):
        self._run(debug=debug)

    def ws_latency(self, target):

        start_time = time.perf_counter()
        self._end_time = None
        self._ping_target = target
        self.sio.emit(
            "started-typing", (self.device_id, self.client_key, "conversation", target)
        )

        time.sleep(2)

        if self._end_time is None:
            self._latency_ws = None
            return "Error"
        else:
            self._latency_ws = (round((self._end_time - start_time) * 100000)) / 100
            return self._latency_ws
