import hashlib
import sqlite3

import pytest

from claimlens import db
from claimlens.api_keys import KeyContext, resolve_api_key, save_user_api_key
from claimlens.auth import hash_password, token_digest, verify_password
from claimlens.config import load_config
from claimlens.kapsule_auth import authenticate, verify_kapsule_password
from claimlens.secrets import SecretError, decrypt_secret, encrypt_secret, mask_secret


def test_password_hash_verification():
    stored = hash_password("correct horse battery")

    assert verify_password("correct horse battery", stored)
    assert not verify_password("wrong horse battery", stored)


def test_authenticated_secret_encryption_round_trip():
    encrypted = encrypt_secret("sk-test-secret", "deploy-secret")

    assert "sk-test-secret" not in encrypted
    assert decrypt_secret(encrypted, "deploy-secret") == "sk-test-secret"
    assert mask_secret("sk-test-secret") == "sk-t...cret"
    with pytest.raises(SecretError):
        decrypt_secret(encrypted, "wrong-secret")


def test_user_api_key_is_encrypted_and_resolved(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(
        database,
        email="user@example.test",
        password_hash=hash_password("correct horse battery"),
    )
    save_user_api_key(
        database,
        user_id=user_id,
        provider="openai",
        value="sk-user-secret",
        deployment_secret="deploy-secret",
    )
    row = db.get_user_api_key(database, user_id=user_id, provider="openai")
    config = load_config(
        env={
            "CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret",
            "CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK": "false",
        }
    )

    assert row is not None
    assert "sk-user-secret" not in row["encrypted_value"]
    assert row["masked_value"] == "sk-u...cret"
    assert (
        resolve_api_key(
            database,
            config,
            provider="openai",
            context=KeyContext(user_id=user_id, request_keys={}),
        )
        == "sk-user-secret"
    )


def test_request_key_wins_and_semantic_can_be_anonymous(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    config = load_config(
        env={
            "OPENAI_API_KEY": "server-key",
            "CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK": "true",
        }
    )

    assert (
        resolve_api_key(
            database,
            config,
            provider="openai",
            context=KeyContext(user_id=None, request_keys={"openai": "guest-key"}),
        )
        == "guest-key"
    )
    assert (
        resolve_api_key(
            database,
            config,
            provider="semantic_scholar",
            context=KeyContext(user_id=None, request_keys={}),
        )
        is None
    )


def test_sessions_store_hashed_token(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(
        database,
        email="user@example.test",
        password_hash=hash_password("correct horse battery"),
    )
    db.create_session(
        database,
        user_id=user_id,
        token_hash=token_digest("session-token"),
        csrf_token="csrf",
        expires_at="2099-01-01 00:00:00",
    )

    session = db.get_session(database, token_digest("session-token"))

    assert session["email"] == "user@example.test"
    assert db.get_session(database, "session-token") is None


def test_kapsule_scrypt_password_verification():
    stored = kapsule_hash("correct horse battery")

    assert verify_kapsule_password("correct horse battery", stored)
    assert not verify_kapsule_password("wrong horse battery", stored)


def test_kapsule_account_authenticates_from_readonly_database(tmp_path):
    kapsule_database = tmp_path / "kapsule.sqlite"
    with sqlite3.connect(kapsule_database) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO users (id, email, role, password_hash) VALUES (?, ?, ?, ?)",
            ("kapsule-user-id", "shared@example.test", "guest", kapsule_hash("kapsulepass")),
        )

    account = authenticate(kapsule_database, "shared@example.test", "kapsulepass")

    assert account is not None
    assert account.id == "kapsule-user-id"
    assert account.email == "shared@example.test"
    assert authenticate(kapsule_database, "shared@example.test", "bad-password") is None


def test_get_or_create_user_provisions_kapsule_account_once(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    first = db.get_or_create_user(
        database,
        email="shared@example.test",
        password_hash="kapsule:kapsule-user-id",
        display_name="shared@example.test",
    )
    second = db.get_or_create_user(
        database,
        email="shared@example.test",
        password_hash="kapsule:kapsule-user-id",
        display_name="shared@example.test",
    )

    assert first == second
    assert db.user_count(database) == 1


def test_config_loads_kapsule_database_path():
    config = load_config(env={"CLAIMLENS_KAPSULE_DB": "/kapsule-data/kapsule.sqlite"})

    assert str(config.web.kapsule_database) == "/kapsule-data/kapsule.sqlite"


def kapsule_hash(password: str) -> str:
    salt = bytes.fromhex("00112233445566778899aabbccddeeff")
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64,
        maxmem=64 * 1024 * 1024,
    )
    return f"scrypt:{salt.hex()}:{digest.hex()}"
