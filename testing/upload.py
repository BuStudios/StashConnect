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
import uuid

import mimetypes
from PIL import Image
import base64
import io

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
target_id = os.getenv("conversation_id")

private_key = None

device_id = "iofsipi09sefisef0s9f"

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "referer": "https://app.schul.cloud/"
}

data = {
    "email": email,
    "password": password,
    "device_id": device_id,
    "app_name": "test",
    "encrypted": "true",
    "callable": "true"
}

response = requests.post("https://api.stashcat.com/auth/login", data=data, headers=headers).json()

client_key = response["payload"]["client_key"]

print(f"Logged in as {response['payload']['userinfo']['first_name']} {response['payload']['userinfo']['last_name']}")


def get_private_key(passphrase):

    global private_key

    if private_key is None:

        print("Fetching private key. Please wait...")

        data = {
            "client_key": client_key,
            "device_id": device_id,  
        }

        response = requests.post("https://api.stashcat.com/security/get_private_key", data=data, headers=headers).json()
        response = json.loads(response["payload"]["keys"]["private_key"])

        private_key = Crypto.PublicKey.RSA.import_key(response["private"], passphrase=passphrase)

    return private_key

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

    decryptor = Crypto.Cipher.PKCS1_OAEP.new(get_private_key(os.getenv("pass2")))
    return decryptor.decrypt(base64.b64decode(encrypted_key))

def encrypt_aes(input, key, iv):
    padded = Crypto.Util.Padding.pad(input, Crypto.Cipher.AES.block_size)
    encryptor = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
    return encryptor.encrypt(padded)


def upload_file(target, file_path, filename=None):
    '''
    -> Main JS of Stashcat
    https://app.stashcat.com/web/main.81e446835bb28e07.js
    '''

    filename = os.path.basename(file_path)

    iv = Crypto.Random.get_random_bytes(16)
    file_key = Crypto.Random.get_random_bytes(32)

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type: content_type = "application/octet-stream"

    max_chunk_size = 5 * 1024 * 1024  # 5MB per chunk
    upload_identifier = str(uuid.uuid4())

    # open the file in binary mode
    with open(file_path, "rb") as file:
        file_content = file.read()

    total_chunks = (len(file_content) + max_chunk_size - 1) // max_chunk_size
    print(f"Total chunks: {total_chunks}")

    for i in range(total_chunks):
        data_chunk = file_content[i*max_chunk_size:(i+1)*max_chunk_size]

        encrypted_chunk = encrypt_aes(data_chunk, file_key, iv)

        data = {
            "resumableChunkNumber": i,
            "resumableChunkSize": max_chunk_size,
            "resumableCurrentChunkSize": len(encrypted_chunk),
            "resumableTotalSize": len(file_content),
            "resumableType": content_type,
            "resumableIdentifier": upload_identifier,
            "resumableFilename": filename,
            "resumableRelativePath": filename,
            "resumableTotalChunks": total_chunks,
            "folder": 0,
            "type": "conversation",
            "type_id": target,
            "encrypted": True,
            "iv": iv.hex(),
            "media_width": None,
            "media_height": None,
            "client_key": client_key,
            "device_id": device_id,
        }

        files={
            "file": ("[object Object]", encrypted_chunk, "application/octet-stream")
        }

        response = requests.post("https://api.stashcat.com/file/upload", data=data, files=files)
        response = response.json()["payload"]["file"]
        
    file_id = response["id"]

    # uploaded file but cant be decrypted since the server does not know the file_key
    iv = Crypto.Random.get_random_bytes(16)

    data = {
        "file_id": response["id"],
        "target": "conversation",
        "target_id": target,
        "key": encrypt_aes(file_key, get_conversation_key(user=target), iv).hex(),
        "iv": iv.hex(),
        "client_key": client_key,
        "device_id": device_id,
    }

    response = requests.post("https://api.stashcat.com/security/set_file_access_key", data=data)
    #print(response.json())


    with Image.open(file_path) as image:
        image = image.convert('RGB')
        min_dimension = min(image.width, image.height)
        scale_factor = 100 / min_dimension

        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left, top = (new_width - 100) / 2, (new_height - 100) / 2
        right, bottom = left + 100, top + 100

        image = image.crop((left, top, right, bottom))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")

        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    data = {
        "client_key": client_key,
        "device_id": device_id,
        "file_id": file_id,
        "content": str("data:image/jpeg;base64," + image_base64)
    }

    response = requests.post("https://api.stashcat.com/file/storePreviewImage", data=data)


upload_file(target_id, "testing/files/glass.jpeg")