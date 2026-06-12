"""
app/core/security.py
─────────────────────
Cryptographic helpers: Spotify token encryption at rest.

Why it exists:
    Spotify access/refresh tokens stored in the DB should not be plaintext.
    This module provides symmetric AES-256 (via Fernet) encryption so tokens
    are opaque blobs in the database.

    We also expose a simple `create_internal_token` / `decode_internal_token`
    pair using python-jose HMAC-SHA256 for any future session cookies or
    API keys we may issue to our own frontend.

How it connects:
    • services/spotify.py  – encrypts tokens before persisting, decrypts before use.
    • dependencies/auth.py – decodes internal tokens from Authorization header.
"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_settings

_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def _fernet() -> Fernet:
    """
    Derive a stable 32-byte Fernet key from SECRET_KEY.

    Fernet needs exactly 32 URL-safe base64-encoded bytes.  We derive this
    deterministically from SECRET_KEY using SHA-256 so we never need a
    separate ENCRYPTION_KEY env var.
    """
    settings = get_settings()
    raw = hashlib.sha256(settings.secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt a Spotify token for storage."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored Spotify token."""
    return _fernet().decrypt(ciphertext.encode()).decode()


# ── Internal JWT helpers ──────────────────────────────────────────────────────

def create_internal_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expire_minutes: int = _DEFAULT_EXPIRE_MINUTES,
) -> str:
    """
    Issue a signed JWT for *our own* frontend (not Spotify tokens).

    `subject` should be the user's UUID string.
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_internal_token(token: str) -> dict[str, Any]:
    """
    Verify and decode our own JWT.  Raises JWTError on invalid/expired tokens.
    """
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
