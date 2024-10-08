import stashconnect
from dotenv import load_dotenv
import os

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
encryption_password = os.getenv("pass2")
target = os.getenv("conversation_id")

client = stashconnect.Client(
    email=email,
    password=password,
    #encryption_password=encryption_password,
    device_id="testid",
    app_name="test",
)

msgs = client.messages.get_messages(target)
for msg in msgs:
    print(msg.longitude)

#@client.event("notification")
#def message_received(data):
#    data.like()
#
#    latency = client.ws_latency(data.type_id)
#
#    if data.type == "conversation" and str(data.type_id) == str(target):
#        data.respond(
#            f"[automated] ↹ websocket_latency = {latency}ms\n| text = {data.content[:50]}...\n| encrypted_text = {data.content_encrypted}",
#            reply_to=data.id,
#        )
#
#    data.unlike()
#
#
#@client.event("user-started-typing")
#def user_typing(data):
#    print("User writing: " + str(data))
#
#
#client.run()
