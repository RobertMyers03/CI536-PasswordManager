import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_salt() -> bytes:
    return os.urandom(16)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=260000,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_password(plaintext: str, key: bytes) -> tuple:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce, ciphertext


def decrypt_password(nonce: bytes, ciphertext: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")