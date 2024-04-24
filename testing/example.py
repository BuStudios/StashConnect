import stashconnect

client = stashconnect.Client(email="email", password="password", encryption_password="passphrase")


@client.event("notification")
def message_received(data):

    message = client.decode_message(target=data["message"]["conversation_id"], text=data["message"]["text"], iv=data["message"]["iv"])

    print(f"Received Message! {message}")
    latency = client.ws_latency(data["message"]["conversation_id"])

    client.send_message(target=data["message"]["conversation_id"], text=f"Message Received! Latency: {latency}ms")


@client.loop(seconds=100)
def loop():
    client.send_message(target="target", text="Loop")

client.run()