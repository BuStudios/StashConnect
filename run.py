import stashconnect
from dotenv import load_dotenv
import os

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
encryption_password = os.getenv("pass2")
target = os.getenv("conversation_id")

user = stashconnect.Login(email=email, password=password, encryption_password=encryption_password)
user.send_message(target=target, text="HEllo")