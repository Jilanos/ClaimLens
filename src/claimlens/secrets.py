"""Small authenticated secret storage helpers.

This avoids a runtime dependency while still ensuring stored keys are encrypted and tamper checked.
The deployment secret must be kept outside SQLite.
"""

from __future__ import annotations

import base64
import hashlib
import secrets as py_secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretError(RuntimeError):
    """Raised when encrypted secret material cannot be used."""


def encrypt_secret(plaintext: str, deployment_secret: str) -> str:
    if not deployment_secret:
        raise SecretError("CLAIMLENS_KEY_ENCRYPTION_SECRET is required to store API keys.")
    nonce = py_secrets.token_bytes(12)
    ciphertext = AESGCM(_derive_aead_key(deployment_secret)).encrypt(
        nonce,
        plaintext.encode("utf-8"),
        b"claimlens-secret-v2",
    )
    return "v2:" + base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_secret(encrypted: str, deployment_secret: str) -> str:
    if not deployment_secret:
        raise SecretError("CLAIMLENS_KEY_ENCRYPTION_SECRET is required to read API keys.")
    if encrypted.startswith("v2:"):
        try:
            raw = base64.urlsafe_b64decode(encrypted[3:].encode("ascii"))
            return AESGCM(_derive_aead_key(deployment_secret)).decrypt(
                raw[:12],
                raw[12:],
                b"claimlens-secret-v2",
            ).decode("utf-8")
        except (ValueError, InvalidTag, UnicodeDecodeError) as exc:
            raise SecretError("Encrypted secret authentication failed.") from exc
    if not encrypted.startswith("v1:"):
        raise SecretError("Unsupported encrypted secret format.")
    try:
        raw = base64.urlsafe_b64decode(encrypted[3:].encode("ascii"))
    except ValueError as exc:
        raise SecretError("Encrypted secret is not valid base64.") from exc
    nonce, tag, ciphertext = raw[:16], raw[16:48], raw[48:]
    key = _derive_key(deployment_secret, nonce)
    import hmac

    expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise SecretError("Encrypted secret authentication failed.")
    return _xor_stream(ciphertext, key).decode("utf-8")


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def redact(text: str) -> str:
    redacted = text
    for marker in ("sk-", "sk-proj-", "ss-", "api_key="):
        if marker in redacted:
            redacted = redacted.replace(marker, "[redacted]-")
    return redacted


def _derive_key(secret: str, nonce: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), nonce, 200_000, dklen=32)


def _derive_aead_key(secret: str) -> bytes:
    return hashlib.sha256(b"claimlens-aead-v2:" + secret.encode("utf-8")).digest()


def _xor_stream(data: bytes, key: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        block = hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        output.extend(block)
        counter += 1
    return bytes(byte ^ stream for byte, stream in zip(data, output, strict=False))
