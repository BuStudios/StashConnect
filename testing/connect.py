import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto.Random
import Crypto.Util
import Crypto.Util.Padding

import requests
from dotenv import load_dotenv
import os
import json
import base64

from datetime import datetime
import time

# load the env file
load_dotenv("config/.env")

# set private login
email = os.getenv("email")
password = os.getenv("password")
target_id = os.getenv("conversation_id")

# the device id can be anything --> to login with set device use the id
device_id = "iofsipi09sefisef0s9f"

print(f"Logging into device {device_id}")

# !! should be expanded
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "referer": "https://app.schul.cloud/"
}

data = {
    "email": email,
    "password": password,
    "device_id": device_id,
    "app_name": "stashconnect:0.1-pre-alpha", # can be anything
    "encrypted": "true", # this is very important
    "callable": "true"
}

# log into account
response = requests.post("https://api.stashcat.com/auth/login", data=data, headers=headers).json()

client_key = response["payload"]["client_key"]
user_id = response["payload"]["userinfo"]["id"]

print(f"Logged in as {response["payload"]["userinfo"]["first_name"]} {response["payload"]["userinfo"]["last_name"]}")

def set_status(status):
    data = {
        "client_key": client_key,
        "device_id": device_id,
        "status": status
    }

    response = requests.post("https://api.stashcat.com/account/change_status", data=data, headers=headers).json()


def get_private_key(passphrase):

    data = {
        "client_key": client_key,
        "device_id": device_id,  
    }

    response = requests.post("https://api.stashcat.com/security/get_private_key", data=data, headers=headers).json()
    response = json.loads(response["payload"]["keys"]["private_key"])

    # imports the RSA key with passphrase for decryption
    return Crypto.PublicKey.RSA.import_key(response["private"], passphrase=passphrase)

def get_conversation_key(user):

    data = {
        "client_key": client_key,
        "device_id": device_id,
        "conversation_id": user
    }

    response = requests.post("https://api.stashcat.com/message/conversation", data=data, headers=headers).json()
    encrypted_key = response["payload"]["conversation"]["key"]

    # decrypt the conversation_key with private key
    decryptor = Crypto.Cipher.PKCS1_OAEP.new(get_private_key(os.getenv("pass2")))
    return decryptor.decrypt(base64.b64decode(encrypted_key))


def send_msg(user, text):

    # get random bytes for the iv
    iv = Crypto.Random.get_random_bytes(16)
    conversation_key = get_conversation_key(user)

    # encode the text into bytes
    text_bytes = text.encode("utf-8")

    # create encryptor object with conversation key and iv
    text_encryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=iv)

    # padd text before AES encryption
    text_padded = Crypto.Util.Padding.pad(text_bytes, Crypto.Cipher.AES.block_size)

    data = {
        "client_key": client_key,
        "device_id": device_id,
        "target": "conversation",
        "conversation_id": user,
        "text": text_encryptor.encrypt(text_padded).hex(), # encrypt the text and convert it to hex
        "files": [],
        "url": [],
        "encrypted": True,
        "iv": iv.hex(), # convert iv to hex
        "verification": "",
        "type": "text",
        "is_forwarded": False
    }

    # send message
    response = requests.post("https://api.stashcat.com/message/send", data=data, headers=headers).json()
    

send_msg(target_id, str(datetime.now())[:19])

# example for a changing status
#while True:
#    set_status(str(datetime.now())[:19])
#    time.sleep(1)