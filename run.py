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
    encryption_password=encryption_password
)

"""
messages = client.messages.get_messages(target)
for message in messages:
    message.like()

sys.exit()
"""


@client.event("notification")
def message_received(data):
    data.like()

    latency = client.ws_latency(data.type_id)

    if data.type == "conversation":
        data.respond(
            f"[automated] ↹ websocket_latency = {latency}ms\n| email = {data.author.email}\n| encrypted_text = {data.content_encrypted}",
            reply_to=data.id,
        )

    data.unlike()


@client.event("user-started-typing")
def user_typing(data):
    print("User writing: " + str(data))


@client.loop(seconds=3000)
def loop():
    pass


client.run()
