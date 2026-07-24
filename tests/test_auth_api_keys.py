import pytest

from claimlens import db
from claimlens.api_keys import KeyContext, resolve_api_key, save_user_api_key
from claimlens.auth import hash_password, token_digest, verify_password
from claimlens.config import load_config
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
