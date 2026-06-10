import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()


def encrypt_api_key(plain_key: str) -> tuple[str, str]:
    key = _derive_key(settings.encryption_key)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plain_key.encode(), None)
    return base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode()


def decrypt_api_key(cipher_b64: str, iv_b64: str) -> str:
    key = _derive_key(settings.encryption_key)
    aesgcm = AESGCM(key)
    ciphertext = base64.b64decode(cipher_b64)
    iv = base64.b64decode(iv_b64)
    return aesgcm.decrypt(iv, ciphertext, None).decode()
