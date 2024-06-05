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


class CryptoUtils:

    def encrypt_aes(plain: bytes, key: bytes, iv: bytes) -> bytes:
        """## Encrypts the provided plaintext using AES.

        #### Args:
            plain (bytes): Plaintext data to be encrypted.
            key (bytes): The key used for AES encryption
            iv (bytes): The iv used for AES encryption. (16 bytes)

        #### Returns:
            bytes: The encrypted data as bytes.
        """
        padded = Crypto.Util.Padding.pad(plain, Crypto.Cipher.AES.block_size)
        encryptor = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
        return encryptor.encrypt(padded)

    def decrypt_aes(encrypted: bytes, key: bytes, iv: bytes) -> bytes:
        """## Decrypts the provided data using AES.

        #### Args:
            encrypted (bytes): The encrypted data to be decrypted.
            key (bytes): The key used for AES decryption.
            iv (bytes): The iv used for AES decryption. (16 bytes)

        #### Returns:
            bytes: The decoded plaintext data.
        """
        decryptor = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
        decrypted = decryptor.decrypt(encrypted)
        return Crypto.Util.Padding.unpad(decrypted, Crypto.Cipher.AES.block_size)

    def decrypt_key(encrypted_key: bytes, private_key: bytes) -> bytes:
        """## Decrypts an RSA-encrypted key.

        #### Args:
            encrypted_key (bytes): The encrypted key data as bytes.
            private_key (bytes): The RSA private key object used for decryption

        #### Returns:
            bytes: The decrypted key as plaintext data.
        """
        decryptor = Crypto.Cipher.PKCS1_OAEP.new(private_key)
        return decryptor.decrypt(base64.b64decode(encrypted_key))

    def load_private_key(encrypted_key: bytes, encryption_password: str):
        """## Imports an RSA private key using a passphrase.

        #### Args:
            encrypted_key (bytes): The encrypted RSA private key.
            encryption_password (str): The passphrase used to decrypt the private key.

        #### Returns:
            The decrypted RSA private key object.
        """
        private_key = Crypto.PublicKey.RSA.import_key(
            encrypted_key, passphrase=encryption_password
        )
        return private_key
