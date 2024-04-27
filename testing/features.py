import stashconnect

client = stashconnect.Client(email="", password="", encryption_password="")

client.messages.send_message(target="", text="", files=[], url="", location=())
client.messages.decode_message(target="", text="", iv="", key="")
client.messages.like_message(message_id="")
client.messages.unlike_message(message_id="")

client.messages.delete_message(message_id="")
client.messages.get_messages(conversation_id="", limit=30, offset=0)

client.users.get_location()
client.users.change_status(status="")
client.users.change_profile_picture(url="")
client.users.reset_profile_picture()

client.conversations.archive_conversation(conversation_id="")

client.files.upload_file(target="", filepath="", encrypted=False)
client.files.download_file(file_id="", directory="")
client.files.file_info(id="")
client.files.delete_files(file_ids="")
client.files.quota()

client.settings.get_notification_count()
client.settings.get_notifications(limit=20, offset=0)

client.settings.change_email(email="")
client.settings.resend_verification_email(email="")
client.settings.change_password(new_password="", old_password="")

client.settings.get_settings()
client.settings.get_me()
client.settings.get_active_devices()

client.tools.get_type(id="")
