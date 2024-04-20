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

class Message:

    def send_message(self, target, text:str):

        iv = Crypto.Random.get_random_bytes(16)
        conversation_key = self.get_conversation_key(target=target)

        text_bytes = text.encode("utf-8")

        text_encryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=iv)

        text_padded = Crypto.Util.Padding.pad(text_bytes, Crypto.Cipher.AES.block_size)

        data = {
            "target": "conversation",
            "conversation_id": target,
            "text": text_encryptor.encrypt(text_padded).hex(),
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
    
    
    def decode_message(self, text, target, iv, key=None):

        conversation_key = self.get_conversation_key(target=target, key=key)
        text_decryptor = Crypto.Cipher.AES.new(conversation_key, Crypto.Cipher.AES.MODE_CBC, iv=bytes.fromhex(iv))

        decrypted_text = text_decryptor.decrypt(bytes.fromhex(text))
        unpadded_text = Crypto.Util.Padding.unpad(decrypted_text, Crypto.Cipher.AES.block_size)

        return unpadded_text.decode("utf-8")