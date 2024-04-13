import stashconnect
from dotenv import load_dotenv
import datetime
import os

load_dotenv("config/.env")

email = os.getenv("email")
password = os.getenv("password")
encryption_password = os.getenv("pass2")
target = os.getenv("conversation_id")

user = stashconnect.Login(email=email, password=password, 
                          #encryption_password=encryption_password
                          )

#while True:
#    text = input("Input:\n")
#    user.send_message(target=target, text=text)

user.change_status(str(datetime.datetime.now())[:19])
user.change_profile_picture(url="https://assets-global.website-files.com/6009ec8cda7f305645c9d91b/620bd6d655f2044afa28bff4_glassmorphism.jpeg")