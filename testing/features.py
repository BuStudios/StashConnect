import stashconnect

client = stashconnect.Client(email="", password="", encryption_password="")

client.send_message(target="", text="", files=[], url="", location=())
client.decode_message(target="", text="", iv="", key="")
client.like_message(message_id="")
client.unlike_message(message_id="")

client.delete_message(message_id="")
client.get_messages(conversation_id="", limit=30, offset=0)

client.get_location()
client.change_status(status="")
client.change_profile_picture(url="")
client.reset_profile_picture()

client.archive_conversation(conversation_id="")

client.upload_file(target="", filepath="", encrypted=False)
client.download_file(file_id="", directory="")
client.file_info(id="")
client.delete_files(file_ids="")
client.quota()

client.get_notification_count()
client.get_notifications(limit=20, offset=0)

client.change_email(email="")
client.resend_verification_email(email="")
client.change_password(new_password="", old_password="")

client.get_settings()
client.get_me()
client.get_active_devices()
client.get_type(id="")
