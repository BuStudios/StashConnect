import requests
import json
import time
import threading
import socketio

from .messages import MessageManager
from .settings import Settings
from .users import UserManager
from .crypto_utils import CryptoUtils
from .conversations import ConversationManager
from .companies import CompanyManager
from .channels import ChannelManager

from .files import Files
from .tools import Tools

from .models import Message

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

    Attributes:
        .email (str): The user's email used for authentication.
        .password (str): The user's password.
        .device_id (str): The device_id used to log in, defaults to "stashconnect123".
        .client_key (str): The key used in submitting requests.
        .socket_id (str): The ID for the websocket connection.
        .user_id (str): The unique ID of the connected user's account.
        .image_url (str): URL to the user's profile image.
        .first_name (str): User's first name.
        .last_name (str): User's last name.
    """

    def __init__(self, *, email, password, encryption_password=None, device_id=None, app_name=None):

        self.messages = MessageManager(self)
        self.tools = Tools(self)
        self.settings = Settings(self)
        self.users = UserManager(self)
        self.files = Files(self)
        self.conversations = ConversationManager(self)
        self.companies = CompanyManager(self)
        self.channels = ChannelManager(self)

        self.email = email
        self.password = password
        self.encryption_password = encryption_password

        self.device_id = "stashconnect" if device_id is None else device_id
        self.app_name = "stashconnect v.0.7.5" if app_name is None else app_name

        self._main_url = "https://api.stashcat.com/"
        self._push_url = "https://push.stashcat.com/"

        self._headers = headers
        self._session = requests.Session()
        self._session.headers.update(self._headers)

        self._login()

        self.conversation_keys = {}
        self.events = {}
        self.loops = []

        self._private_key = None
        self._ping_target = None
        self._end_time = None
        self._latency_ws = None

        if encryption_password is not None:
            self.get_private_key(encryption_password=self.encryption_password)

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

        if self.encryption_password is None:
            print(
                f"Logged in as {self.first_name} {self.last_name}! "
                "No encryption password was provided so some features won't work"
            )
        else:
            print(f"Logged in as {self.first_name} {self.last_name}!")

        return response

    def _post(self, url, *, data, auth=True, return_all=False, **kwargs):

        data["device_id"] = self.device_id

        if auth is True:
            data["client_key"] = self.client_key

        response = self._session.post(f"{self._main_url}{url}", data=data, **kwargs)

        response.raise_for_status()

        if not return_all:
            response = response.json()
            status = response["status"]
            payload = response["payload"]

            if status["value"] != "OK":
                # create custom exceptions
                raise Exception(status["message"])

            return payload

        else:
            return response

    def verify_login(self):

        data = {"app_name": self.app_name, "encrypted": True, "callable": True}

        response = self._post("/auth/check", data=data)
        return response

    def get_private_key(self, *, encryption_password: str) -> None:

        print("Importing private key. Please wait...")
        response = self._post("security/get_private_key", data={})
        encrypted_key = json.loads(response["keys"]["private_key"])

        self._private_key = CryptoUtils.load_private_key(
            encrypted_key["private"], encryption_password
        )

    def get_conversation_key(self, target, target_type, key=None):

        if self._private_key is None:
            return None

        try:
            return self.conversation_keys[target]
        except KeyError:
            encrypted_key = key

            if encrypted_key is None:
                if target_type == "conversation":
                    response = self._post(
                        "message/conversation", data={"conversation_id": target}
                    )
                    encrypted_key = response["conversation"]["key"]
                else:
                    response = self._post(
                        "channels/info",
                        data={"channel_id": target, "without_members": True},
                    )
                    encrypted_key = response["channels"]["key"]

            decrypted_key = CryptoUtils.decrypt_key(encrypted_key, self._private_key)

            self.conversation_keys[target] = decrypted_key
            return self.conversation_keys[target]

    def event(self, name):

        def decorator(func):
            def wrapper(*args):

                if func.__name__ == "message_received":
                    func(Message(self, args[0]["message"]))

                else:
                    if len(args) == 1:
                        func(args[0])
                    else:
                        func(args)

            self.events[name] = wrapper
            return wrapper

        return decorator

    def loop(self, seconds):
        def decorator(func):
            def wrapped_func():
                def run():
                    time.sleep(2)
                    while True:
                        func()
                        time.sleep(seconds)

                return run

            self.loops.append(wrapped_func())
            return func

        return decorator

    def event_modifier(self):
        def decorator(func):
            def wrapper(*args):
                if str(args[2]) == str(self.user_id) and str(args[1]) == str(
                    self._ping_target
                ):
                    self._end_time = time.perf_counter()
                func(*args)

            return wrapper

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

        for event_name, event_handler in self.events.items():
            if event_name == "user-started-typing":
                event_modifier = self.event_modifier()(event_handler)
                self.sio.on(event_name)(event_modifier)
            else:
                self.sio.on(event_name)(event_handler)

        self.sio.connect(self._push_url)
        self.sio.wait()

    def run(self, debug=False):
        self._run_loops()
        if len(self.events) != 0:
            self._run(debug=debug)

    def _run_loops(self):
        for loop in self.loops:
            thread = threading.Thread(target=loop)
            thread.start()

    def ws_latency(self, target):
        target_type = self.tools.get_type(target)

        start_time = time.perf_counter()
        self._end_time = None
        self._ping_target = target

        self.sio.emit("started-typing", (self.device_id, self.client_key, target_type, target))

        time.sleep(2)

        if self._end_time is None:
            self._latency_ws = None
            return "[Error]"
        else:
            self._latency_ws = (round((self._end_time - start_time) * 100000)) / 100
            return self._latency_ws
