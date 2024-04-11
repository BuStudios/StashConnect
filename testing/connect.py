import requests
import uuid
import datetime
import time
from dotenv import load_dotenv
import os

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
device_id = "iofsipi09sefisef0s9f"
print(f"Logging in with device id {device_id}")

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "referer": "https://app.schul.cloud/"
}

data = {
    "email": email,
    "password": password,
    "device_id": device_id,
    "app_name": "Main123",
    "encrypted": "true",
    "callable": "true"
}

response = requests.post("https://api.stashcat.com/auth/login", data=data, headers=headers).json()
client_key = response["payload"]["client_key"]
user_id = response["payload"]["userinfo"]["id"]

print(f"Logged in as {response["payload"]["userinfo"]["first_name"]} {response["payload"]["userinfo"]["last_name"]}")
print(client_key)
while True:
    data = {
        "client_key": client_key,
        "device_id": device_id,
        "status": str(datetime.datetime.now())[:19]
    }

    response = requests.post("https://api.stashcat.com/account/change_status", data=data, headers=headers).json()
    print(response)
    time.sleep(2)