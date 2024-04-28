import stashconnect
from dotenv import load_dotenv
import sys
import os
import pprint
import time

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
encryption_password = os.getenv("pass2")
target = os.getenv("conversation_id")

client = stashconnect.Client(
    email=email, password=password, 
    #encryption_password=encryption_password
)


message = client.messages.send_message(target, "hello1", encrypted=False)
print(message.author.first_name)
message.like()
sys.exit()

@client.event("notification")
def message_received(data):
    message = client.messages.decode_message(
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

    print(client.messages.like_message(data["message"]["id"]))

    latency = client.ws_latency(data["message"]["conversation_id"])

    client.messages.send_message(
        target=data["message"]["conversation_id"],
        text=f"[automated] msg received => ↹ websocket_latency = {latency}ms.\nreceived: {message}. author: {sender}. UNIX: {timestamp}.",
        reply_to=data["message"]["id"],
    )


@client.event("user-started-typing")
def user_typing(data):
    print("User writing: " + str(data))


@client.loop(seconds=30)
def loop():
    client.messages.send_message(target, "200 ping")


client.run()
