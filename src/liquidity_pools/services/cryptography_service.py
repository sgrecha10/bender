import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class CryptographyService:
    @classmethod
    def encrypt_private_key(cls, private_key: str) -> dict:
        aesgcm = AESGCM(base64.b64decode(settings.MASTER_KEY))

        # GCM standard nonce size = 12 bytes
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(
            nonce=nonce,
            data=private_key.encode(),
            associated_data=None
        )

        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "version": 1
        }

    @classmethod
    def decrypt_private_key(cls, payload: dict) -> str:
        aesgcm = AESGCM(base64.b64decode(settings.MASTER_KEY))

        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])

        plaintext = aesgcm.decrypt(
            nonce=nonce,
            data=ciphertext,
            associated_data=None
        )

        return plaintext.decode()
