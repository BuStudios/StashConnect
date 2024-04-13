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
import pprint

from datetime import datetime
import time

import socketio

# load the env file
load_dotenv("config/.env")

# set private login
email = os.getenv("email")
password = os.getenv("password")
target_id = os.getenv("conversation_id")

private_key = None

# the device id can be anything --> to login with set device use the id
device_id = "iofsipi09sefisef0s9f"

# !! should be expanded
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "referer": "https://app.schul.cloud/"
}

data = {
    "email": email,
    "password": password,
    "device_id": device_id,
    "app_name": "stashconnect:alpha", # can be anything
    "encrypted": "true", # this is very important
    "callable": "true"
}

# log into account
response = requests.post("https://api.stashcat.com/auth/login", data=data, headers=headers).json()

client_key = response["payload"]["client_key"]
user_id = response["payload"]["userinfo"]["id"]
socket_id = response["payload"]["userinfo"]["socket_id"]

print(f"\nLogged in as {response["payload"]["userinfo"]["first_name"]} {response["payload"]["userinfo"]["last_name"]}\n")

def set_status(status):
    data = {
        "client_key": client_key,
        "device_id": device_id,
        "status": status
    }

    response = requests.post("https://api.stashcat.com/account/change_status", data=data, headers=headers).json()


def get_private_key(passphrase):

    # save the private key since it takes a long time to process

    global private_key

    if private_key is None:

        print("fetching private key. please wait...")
        data = {
            "client_key": client_key,
            "device_id": device_id,  
        }

        response = requests.post("https://api.stashcat.com/security/get_private_key", data=data, headers=headers).json()
        response = json.loads(response["payload"]["keys"]["private_key"])

        # imports the RSA key with passphrase for decryption
        private_key = Crypto.PublicKey.RSA.import_key(response["private"], passphrase=passphrase)
        return private_key
    else:
        return private_key

# fetch private key at beginning to process text much faster
get_private_key(os.getenv("pass2"))

def get_conversation_key(user, key = None):

    encrypted_key = key

    if key == None:
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
    

#send_msg(target_id, str(datetime.now())[:19])

# example for a changing status
#while True:
#    set_status(str(datetime.now())[:19])
#    time.sleep(1)

# message decoder
def decode_message(text, iv, user, key = None):
    conversation_key = get_conversation_key(user, key=key)

    # creates a decryptor object with key and converted iv
    text_decryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=bytes.fromhex(iv))

    # decrypt converted text and unpadd it
    decrypted_text = text_decryptor.decrypt(bytes.fromhex(text))
    unpadded_text = Crypto.Util.Padding.unpad(decrypted_text, Crypto.Cipher.AES.block_size)

    # decode text to utf-8
    return unpadded_text.decode("utf-8")


sio = socketio.Client(
    #logger=True, 
    #engineio_logger=True
)

@sio.event
def connect():

    print("Connected to server.")

    data = {
        "hidden_id": socket_id,
        "device_id": device_id,
        "client_key": client_key
    }

    sio.emit("userid", data)

    #while True:
    #    
    #    # sends a websocket event
    #    sio.emit("started-typing", (device_id, client_key, "conversation", target_id))

    #    time.sleep(5)

@sio.on("*")
def event(*args):
    blacklist = [
        "online_status_change", "user-started-typing", "message_changed", "object_change"
    ]

    if args[0] in blacklist:
        return
    
    elif args[0] == "new_device_connected":
        print(f"A new device with the IP address {args[1]["ip_address"]} has connected to your account.")
        return
    
    elif args[0] == "message_sync":
        return
        print(f"MSG SENT!")
        print(decode_message(args[1]["text"], args[1]["iv"], args[1]["conversation_id"]))
        return
    
    elif args[0] == "notification":
        message = decode_message(args[1]["message"]["text"], args[1]["message"]["iv"], args[1]["message"]["conversation_id"], args[1]["conversation"]["key"])
        print(f"MSG RECEIVED! {message}")

        if message == "/help":
            send_msg(args[1]["message"]["conversation_id"], "[automated] in development 🤖 [check github.com/bustudios/stashconnect]")
        else:
            send_msg(args[1]["message"]["conversation_id"], "[automated] message recieved 👍")

        return
    
    pprint.pprint(args)

@sio.event
def disconnect():
    print("Disconnected from server.")

sio.connect("https://push.stashcat.com/")
sio.wait()