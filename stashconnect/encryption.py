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

import base64
import json


class Encryption:

    def encrypt_aes(plain: bytes, key: bytes, iv: bytes):
        padded = Crypto.Util.Padding.pad(plain, Crypto.Cipher.AES.block_size)
        encryptor = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
        return encryptor.encrypt(padded)

    def decrypt_aes(encrypted: bytes, key: bytes, iv: bytes) -> str:
        decryptor = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
        decrypted = decryptor.decrypt(encrypted)
        return Crypto.Util.Padding.unpad(decrypted, Crypto.Cipher.AES.block_size)

    def decrypt_key(encrypted_key: bytes, private_key: bytes) -> str:
        decryptor = Crypto.Cipher.PKCS1_OAEP.new(private_key)
        return decryptor.decrypt(base64.b64decode(encrypted_key))

    def load_private_key(self, encryption_password: str):
        response = self._post("security/get_private_key", data={})
        response = json.loads(response["keys"]["private_key"])
        private_key = Crypto.PublicKey.RSA.import_key(
            response["private"], passphrase=encryption_password
        )
        return private_key
