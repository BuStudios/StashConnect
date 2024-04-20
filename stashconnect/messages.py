import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Cipher.PKCS1_OAEP
import Crypto.Protocol
import Crypto.PublicKey
import Crypto.PublicKey.RSA
import Crypto

import Crypto.Random
import Crypto.Util
import Crypto.Util.Padding

from .encryption import Encryption

class Message:

    def send_message(self, target, text:str):

        iv = Crypto.Random.get_random_bytes(16)
        conversation_key = self.get_conversation_key(target=target)

        text_bytes = text.encode("utf-8")
        text = Encryption.encrypt_aes(text_bytes, conversation_key, iv)

        data = {
            "target": "conversation",
            "conversation_id": target,
            "text": text.hex(),
            "files": [],
            "url": [],
            "encrypted": True,
            "iv": iv.hex(),
            "verification": "",
            "type": "text",
            "is_forwarded": False
        }

        response = self._post("message/send", data=data)
        return response
    
    
    def decode_message(self, *, target, text, iv, key=None):

        conversation_key = self.get_conversation_key(target=target, key=key)
        text = Encryption.decrypt_aes(bytes.fromhex(text), conversation_key, bytes.fromhex(iv))

        return text.decode("utf-8")