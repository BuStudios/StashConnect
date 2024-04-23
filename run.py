import stashconnect
from dotenv import load_dotenv
import datetime
import os
import time
import pprint
import sys

load_dotenv("config/.env")

email = os.getenv("email")
email2 = os.getenv("email2")
password = os.getenv("password")
encryption_password = os.getenv("pass2")
target = os.getenv("conversation_id")

client = stashconnect.Client(
    email=email, password=password, encryption_password=encryption_password
)

# client.upload_file(target, "testing/files/rick.gif")
# print(client.send_message(target, "hi", "testing/files/bee.png"))
# print(client.get_messages(target, limit=1, offset=1))
# print(client.get_location())
# print(client.verify_login())
# print(client.get_active_devices())
# print(client.get_me())
# print(client.get_settings())
# print(client.change_password(password, password))
# pprint.pprint(client.get_notifications())
# print(client.change_email(email))
# time.sleep(5)
# print(client.resend_verification_email(email))

# print(client.send_message(target, "test", True))

# sys.exit()

# while True:
#    text = input("Input:\n")
#    client.send_message(target=target, text=text)

# client.change_status(str(datetime.datetime.now())[:19])
# print(client.change_profile_picture(url="https://assets-global.website-files.com/6009ec8cda7f305645c9d91b/620bd6d655f2044afa28bff4_glassmorphism.jpeg"))


@client.event("notification")
def message_received(data):
    message = client.decode_message(
        target=data["message"]["conversation_id"],
        text=data["message"]["text"],
        iv=data["message"]["iv"],
        key=data["conversation"]["key"],
    )

    sender = (
        data["message"]["sender"]["first_name"],
        data["message"]["sender"]["last_name"],
    )
    timestamp = data["message"]["time"]

    print(f"Message received: {message}. Author: {sender}. UNIX: {timestamp}.")

    # client.sio.emit("started-typing", (client.device_id, client.client_key, "conversation", data["message"]["conversation_id"]))

    latency = client.ws_latency(data["message"]["conversation_id"])

    client.send_message(
        target=data["message"]["conversation_id"],
        text=f"[automated] msg received => ↹ websocket_latency = {latency}ms.\nreceived: {message}. author: {sender}. UNIX: {timestamp}.",
    )

@client.event("user-started-typing")
def user_typing(data):
    print("User writing: " + data)

client.run(debug=False)
