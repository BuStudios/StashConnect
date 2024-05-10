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
target_channel = os.getenv("channel_id")

client = stashconnect.Client(
    email=email, password=password,
    encryption_password=encryption_password,
    device_id="99dme98fsefmf8fuscpdu",
    app_name="maintest",
)

#members = client.channels.members(target_channel)
#for member in members:
#    print(member.first_name)

channels = client.channels.joined("")
pprint.pprint(channels)

sys.exit()

company = client.companies.member()
print(company[0].manager.permissions)
sys.exit()

#print(client.conversations.disable_notifications(target, "100"))
#print(client.conversations.enable_notifications(target))

print(client.conversations.favorite(target))
conversation = client.conversations.get(target)
print(conversation.members[0].first_name)
print(conversation.favorite())
conversation.disable_notifications("20")
sys.exit()

"""
messages = client.messages.get_flagged(target)
for message in messages:
    print(message.content)
    message.unflag()
sys.exit()
"""


@client.event("notification")
def message_received(data):
    data.like()

    latency = client.ws_latency(data.type_id)

    if data.type == "conversation" and str(data.type_id) == str(target):
        data.respond(
            f"[automated] ↹ websocket_latency = {latency}ms\n| text = {data.content[:50]}...\n| encrypted_text = {data.content_encrypted}",
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
