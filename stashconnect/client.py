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

    """
    Represents a client connection to Stashcat API.

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

        ._private_key (Crypto.PublicKey.RSA): The RSA private key used to decrypt conversation keys.

    Methods:

        .send_message(target, text). Encrypts and sends a message to a specific conversation.

        .decode_message(text, target, iv, key -> optional): Decrypts an encrypted message.

        .change_profile_picture(url): Updates the user's profile image with an image URL.

        .change_status(status): Updates the user's status.
    """

    def __init__(self, *, email, password, device_id=None, encryption_password=None):

        self.conversation_keys = {}
        self.events = {}

        self.email = email
        self.password = password
        self.device_id = "stashconnect123" if device_id is None else device_id

        self._main_url = "https://api.stashcat.com/"
        self._push_url = "https://push.stashcat.com/"

        self._headers = headers

        data = {
            "email": self.email,
            "password": self.password,
            "app_name": "stashconnect:alpha",
            "encrypted": "true",
            "callable": "true"
        }

        response = self._post("auth/login", data=data, auth=False)

        self.client_key = response["client_key"]
        self.socket_id = response["userinfo"]["socket_id"]
        self.user_id = response["userinfo"]["id"]
        self.image_url = response["userinfo"]["image"]

        self.first_name = response["userinfo"]["first_name"]
        self.last_name = response["userinfo"]["last_name"]

        print(f"Logged in as {self.first_name} {self.last_name}!")

        self._private_key = None
        self._ping_target = None

        if encryption_password is not None:
            self.get_private_key(encryption_password=encryption_password)


    def _post(self, url, *, data, auth=True):

        data["device_id"] = self.device_id

        if auth is True:
            data["client_key"] = self.client_key

        response = requests.post(f"{self._main_url}{url}", data=data, headers=self._headers)
        
        response.raise_for_status()
        
        response = response.json()
        status = response["status"]
        payload = response["payload"]

        if status["value"] != "OK":
            # make own exceptions
            raise Exception(status["message"])

        return payload
    

    def get_private_key(self, *, encryption_password:str):

        print("Importing private key. Please wait...")

        response = self._post("security/get_private_key", data={})
        response = json.loads(response["keys"]["private_key"])

        self._private_key = Crypto.PublicKey.RSA.import_key(response["private"], passphrase=encryption_password)


    def get_conversation_key(self, target, key=None):

        try:
            return self.conversation_keys[target]
        except KeyError:
            encrypted_key = key

            if encrypted_key is None:

                response = self._post("message/conversation", data={"conversation_id": target})
                encrypted_key = response["conversation"]["key"]

            decryptor = Crypto.Cipher.PKCS1_OAEP.new(self._private_key)
            decrypted_key = decryptor.decrypt(base64.b64decode(encrypted_key))

            self.conversation_keys[target] = decrypted_key
            return self.conversation_keys[target]
        

    def send_message(self, target, text:str):

        iv = Crypto.Random.get_random_bytes(16)
        conversation_key = self.get_conversation_key(target=target)

        text_bytes = text.encode("utf-8")

        text_encryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=iv)

        text_padded = Crypto.Util.Padding.pad(text_bytes, Crypto.Cipher.AES.block_size)

        data = {
            "target": "conversation",
            "conversation_id": target,
            "text": text_encryptor.encrypt(text_padded).hex(),
            "files": [],
            "url": [],
            "encrypted": True,
            "iv": iv.hex(),
            "verification": "",
            "type": "text",
            "is_forwarded": False
        }

        response = self._post("message/send", data=data)
        return response


    def decode_message(self, text, target, iv, key=None):

        conversation_key = self.get_conversation_key(target=target, key=key)
        text_decryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=bytes.fromhex(iv))

        decrypted_text = text_decryptor.decrypt(bytes.fromhex(text))
        unpadded_text = Crypto.Util.Padding.unpad(decrypted_text, Crypto.Cipher.AES.block_size)

        return unpadded_text.decode("utf-8")
    

    def change_status(self, status):

        response = self._post("account/change_status", data={"status": status})
        return response
    

    def change_profile_picture(self, *, url):
        
        response = requests.get(url)
        response.raise_for_status()
        

        with Image.open(io.BytesIO(response.content)) as image:

            min_dimension = min(image.width, image.height)

            scale_factor = 512 / min_dimension

            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left, top = (new_width - 512) / 2, (new_height - 512) / 2
            right, bottom = left + 512, top + 512

            image = image.crop((left, top, right, bottom))

            buffered = io.BytesIO()
            image.save(buffered, format="PNG")

            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            response = self._post("account/store_profile_image", data={"imgBase64": f"data:image/png;base64,{image_base64}"})
            return response
        

    def reset_profile_picture(self):

        response = self._post("account/reset_profile_image", data={})
        return response


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
                "client_key": self.client_key
            }

            self.sio.emit("userid", data)

        @self.sio.event
        def disconnect():
            print("Disconnected from the server")
            self.sio.disconnect()

        @self.sio.on("user-started-typing")
        def pong(*args):
            if str(args[2]) == str(self.user_id) and str(args[1]) == str(self._ping_target):
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
        self.sio.emit("started-typing", (self.device_id, self.client_key, "conversation", target))

        time.sleep(2)

        if self._end_time is None:
            self._latency_ws = None
            return "Error"
        else:
            self._latency_ws = (round((self._end_time - start_time) * 100000)) / 100
            return self._latency_ws