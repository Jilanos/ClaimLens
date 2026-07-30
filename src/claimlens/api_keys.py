"""API key persistence and resolution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from claimlens import db
from claimlens.config import AppConfig
from claimlens.secrets import SecretKeyring, decrypt_secret, encrypt_secret, mask_secret

PROVIDERS = {"openai", "semantic_scholar", "ncbi"}


class ApiKeyTestError(ValueError):
    """Raised when a provider rejects or cannot validate an API key."""


@dataclass(frozen=True)
class KeyContext:
    user_id: int | None
    request_keys: dict[str, str]


@dataclass(frozen=True)
class SupadataKeyCandidate:
    id: int
    api_key: str
    fingerprint: str
    masked_value: str


def save_user_api_key(
    database_path: Path | str,
    *,
    user_id: int,
    provider: str,
    value: str,
    deployment_secret: str | SecretKeyring | None,
) -> None:
    provider = _provider(provider)
    clean_value = value.strip()
    encrypted = encrypt_secret(clean_value, deployment_secret or "")
    db.upsert_user_api_key(
        database_path,
        user_id=user_id,
        provider=provider,
        encrypted_value=encrypted,
        key_fingerprint=_fingerprint(clean_value),
        masked_value=mask_secret(clean_value),
    )


def resolve_api_key(
    database_path: Path | str,
    config: AppConfig,
    *,
    provider: str,
    context: KeyContext,
) -> str | None:
    provider = _provider(provider)
    request_value = context.request_keys.get(provider, "").strip()
    if request_value:
        return request_value
    if context.user_id is not None:
        row = db.get_user_api_key(database_path, user_id=context.user_id, provider=provider)
        if row is not None:
            return decrypt_secret(row["encrypted_value"], keyring_for_config(config))
    if config.web.allow_server_api_key_fallback:
        return _server_key(config, provider)
    return None


def keyring_for_config(config: AppConfig) -> SecretKeyring:
    return SecretKeyring(
        config.web.key_encryption_key_id,
        config.web.key_encryption_secret or "",
        config.web.key_encryption_previous,
    )


def rotate_stored_api_keys(database_path: Path | str, *, keyring: SecretKeyring) -> int:
    """Re-encrypt all persisted API keys atomically with the active v3 key."""
    from contextlib import closing

    with closing(db.connect(database_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            rows = []
            for table in ("user_api_keys", "supadata_api_keys"):
                for row in connection.execute(
                    f"SELECT id, encrypted_value FROM {table}"
                ).fetchall():
                    rows.append(
                        (table, int(row["id"]), decrypt_secret(row["encrypted_value"], keyring))
                    )
            for table, row_id, plaintext in rows:
                connection.execute(
                    f"UPDATE {table} SET encrypted_value = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (encrypt_secret(plaintext, keyring), row_id),
                )
            connection.commit()
            return len(rows)
        except Exception:
            connection.rollback()
            raise


def _server_key(config: AppConfig, provider: str) -> str | None:
    if provider == "openai":
        return config.api_keys.openai
    if provider == "semantic_scholar":
        return config.api_keys.semantic_scholar
    if provider == "ncbi":
        return config.api_keys.ncbi
    return None


def _provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in PROVIDERS:
        raise ValueError(f"Unsupported API key provider: {provider}")
    return normalized


def validate_provider_api_key(provider: str, api_key: str, *, timeout: float = 10.0) -> None:
    """Run a minimal authenticated provider request and raise on non-success."""
    provider = _provider(provider)
    if not api_key.strip():
        raise ApiKeyTestError("The API key is empty.")
    if provider == "openai":
        request = Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
    elif provider == "semantic_scholar":
        query = urlencode({"query": "test", "limit": "1"})
        request = Request(
            f"https://api.semanticscholar.org/graph/v1/paper/search?{query}",
            headers={"x-api-key": api_key},
        )
    else:
        query = urlencode(
            {
                "db": "pubmed",
                "term": "test",
                "retmode": "json",
                "retmax": "0",
                "api_key": api_key,
            }
        )
        request = Request(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{query}")
    try:
        with urlopen(request, timeout=timeout) as response:
            if not 200 <= response.status < 300:
                raise ApiKeyTestError(f"{provider} returned HTTP {response.status}.")
            if provider != "ncbi":
                json.loads(response.read())
    except HTTPError as exc:
        raise ApiKeyTestError(f"{provider} rejected the key (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise ApiKeyTestError(f"{provider} key test failed: {exc}") from exc


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def save_supadata_api_key(
    database_path: Path | str,
    *,
    user_id: int,
    label: str,
    value: str,
    priority: int,
    deployment_secret: str | SecretKeyring | None,
) -> int:
    clean_value = value.strip()
    encrypted = encrypt_secret(clean_value, deployment_secret or "")
    return db.create_supadata_api_key(
        database_path,
        user_id=user_id,
        label=label,
        priority=priority,
        encrypted_value=encrypted,
        key_fingerprint=_fingerprint(clean_value),
        masked_value=mask_secret(clean_value),
    )


def eligible_supadata_keys(
    database_path: Path | str,
    *,
    user_id: int | None,
    deployment_secret: str | SecretKeyring | None,
    monthly_cap: int,
) -> list[SupadataKeyCandidate]:
    if user_id is None:
        return []
    rows = db.list_eligible_supadata_api_keys(
        database_path,
        user_id=user_id,
        billing_period=current_billing_period(),
        monthly_cap=monthly_cap,
    )
    candidates: list[SupadataKeyCandidate] = []
    for row in rows:
        candidates.append(
            SupadataKeyCandidate(
                id=int(row["id"]),
                api_key=decrypt_secret(row["encrypted_value"], deployment_secret or ""),
                fingerprint=row["key_fingerprint"],
                masked_value=row["masked_value"],
            )
        )
    return candidates


def current_billing_period(now: datetime | None = None) -> str:
    value = now or datetime.now(UTC)
    return value.strftime("%Y-%m")


def next_billing_period_start(now: datetime | None = None) -> str:
    value = now or datetime.now(UTC)
    if value.month == 12:
        reset = value.replace(year=value.year + 1, month=1, day=1)
    else:
        reset = value.replace(month=value.month + 1, day=1)
    reset = reset.replace(hour=0, minute=0, second=0, microsecond=0)
    return reset.strftime("%Y-%m-%d %H:%M:%S")
