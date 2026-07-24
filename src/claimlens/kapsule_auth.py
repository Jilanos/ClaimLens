"""Read-only authentication bridge for existing Kapsule accounts."""

from __future__ import annotations

import hashlib
import hmac
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KapsuleAccount:
    id: str
    email: str
    role: str


def authenticate(
    database_path: Path | str | None,
    email: str,
    password: str,
) -> KapsuleAccount | None:
    """Return the matching Kapsule account when credentials are valid.

    The Kapsule database is mounted read-only in production. Authentication only
    reads the `users` table and never creates sessions or modifies Kapsule state.
    """

    if database_path is None or not email.strip() or not isinstance(password, str):
        return None
    path = Path(database_path)
    if not path.exists():
        return None

    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT id, email, role, password_hash
                FROM users
                WHERE email = ?
                """,
                (email.strip().lower(),),
            ).fetchone()
    except sqlite3.Error:
        return None

    if row is None or not verify_kapsule_password(password, row["password_hash"]):
        return None
    return KapsuleAccount(id=str(row["id"]), email=row["email"], role=row["role"])


def verify_kapsule_password(password: str, stored: str) -> bool:
    """Verify Kapsule's `scrypt:<salt hex>:<hash hex>` password format."""

    try:
        algorithm, salt_hex, hash_hex = str(stored).split(":", 2)
        if algorithm != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (TypeError, ValueError):
        return False

    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=len(expected),
        maxmem=64 * 1024 * 1024,
    )
    return hmac.compare_digest(actual, expected)
