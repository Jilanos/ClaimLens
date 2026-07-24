"""API key persistence and resolution."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from claimlens import db
from claimlens.config import AppConfig
from claimlens.secrets import decrypt_secret, encrypt_secret, mask_secret

PROVIDERS = {"openai", "semantic_scholar", "ncbi"}


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
    deployment_secret: str | None,
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
            return decrypt_secret(row["encrypted_value"], config.web.key_encryption_secret or "")
    if config.web.allow_server_api_key_fallback:
        return _server_key(config, provider)
    return None


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


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def save_supadata_api_key(
    database_path: Path | str,
    *,
    user_id: int,
    label: str,
    value: str,
    priority: int,
    deployment_secret: str | None,
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
    deployment_secret: str | None,
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
