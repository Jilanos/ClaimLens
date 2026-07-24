"""Configuration loading for ClaimLens."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PathsConfig:
    database: Path
    outputs: Path
    transcripts: Path
    briefs: Path


@dataclass(frozen=True)
class PipelineConfig:
    max_videos_per_channel: int
    candidate_min_duration_seconds: int
    source_verification_max_results: int
    source_verification_timeout_seconds: int
    analysis_max_chars: int
    report_language: str


@dataclass(frozen=True)
class TranscriptConfig:
    provider_order: tuple[str, ...]
    supadata_monthly_request_cap: int
    supadata_language: str | None


@dataclass(frozen=True)
class WebConfig:
    max_request_bytes: int
    rate_limit_actions: int
    rate_limit_window_seconds: int
    public_base_url: str | None
    secure_cookies: bool
    registration_enabled: bool
    allow_server_api_key_fallback: bool
    key_encryption_secret: str | None
    kapsule_database: Path | None


@dataclass(frozen=True)
class SourceConfig:
    advanced_source_verification: bool
    enable_pubmed: bool
    enable_semantic_scholar: bool
    enable_web_search: bool


@dataclass(frozen=True)
class ApiKeys:
    youtube: str | None
    openai: str | None
    semantic_scholar: str | None
    ncbi: str | None


@dataclass(frozen=True)
class AppConfig:
    repo_root: Path
    paths: PathsConfig
    pipeline: PipelineConfig
    transcripts: TranscriptConfig
    web: WebConfig
    sources: SourceConfig
    api_keys: ApiKeys


DEFAULT_CONFIG_PATH = Path("config/claimlens.example.toml")
CONFIG_ENV = "CLAIMLENS_CONFIG"


class ConfigError(ValueError):
    """Raised when local ClaimLens configuration is invalid."""


def load_config(
    config_path: Path | str | None = None,
    *,
    env: dict[str, str] | None = None,
) -> AppConfig:
    """Load config from TOML plus environment variables."""

    environ = os.environ if env is None else env
    explicit_config = Path(config_path) if config_path else _optional_env_path(environ, CONFIG_ENV)
    repo_root = Path.cwd()
    raw = _read_toml(explicit_config or repo_root / DEFAULT_CONFIG_PATH)
    config_base = explicit_config.expanduser().parent if explicit_config else None

    paths = raw.get("paths", {})
    pipeline = raw.get("pipeline", {})
    transcripts_config = raw.get("transcripts", {})
    web = raw.get("web", {})
    sources = raw.get("sources", {})

    database = _env_path(
        environ,
        "CLAIMLENS_DB",
        _config_path(paths.get("database", "data/claimlens.sqlite3"), base=config_base),
    )
    outputs = _env_path(
        environ,
        "CLAIMLENS_OUTPUTS",
        _config_path(paths.get("outputs", "outputs"), base=config_base),
    )
    transcripts = _env_path(
        environ,
        "CLAIMLENS_TRANSCRIPTS",
        _config_path(paths.get("transcripts", "outputs/transcripts"), base=config_base),
    )
    briefs = _env_path(
        environ,
        "CLAIMLENS_BRIEFS",
        _config_path(paths.get("briefs", "outputs/briefs"), base=config_base),
    )

    return AppConfig(
        repo_root=repo_root,
        paths=PathsConfig(
            database=database,
            outputs=outputs,
            transcripts=transcripts,
            briefs=briefs,
        ),
        pipeline=PipelineConfig(
            max_videos_per_channel=_int_setting(
                pipeline,
                "max_videos_per_channel",
                10,
            ),
            candidate_min_duration_seconds=_int_setting(
                pipeline,
                "candidate_min_duration_seconds",
                480,
            ),
            source_verification_max_results=_int_setting(
                pipeline,
                "source_verification_max_results",
                5,
            ),
            source_verification_timeout_seconds=_int_setting(
                pipeline,
                "source_verification_timeout_seconds",
                20,
            ),
            analysis_max_chars=_int_setting(pipeline, "analysis_max_chars", 60000),
            report_language=str(pipeline.get("report_language", "en")).strip() or "en",
        ),
        transcripts=TranscriptConfig(
            provider_order=_provider_order(
                environ.get("CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER")
                or transcripts_config.get("provider_order", "youtube")
            ),
            supadata_monthly_request_cap=_int_setting(
                transcripts_config,
                "supadata_monthly_request_cap",
                100,
            ),
            supadata_language=_optional_string(
                environ.get("CLAIMLENS_SUPADATA_LANGUAGE")
                or transcripts_config.get("supadata_language")
            ),
        ),
        web=WebConfig(
            max_request_bytes=_int_setting(web, "max_request_bytes", 16_384),
            rate_limit_actions=_int_setting(web, "rate_limit_actions", 12),
            rate_limit_window_seconds=_int_setting(web, "rate_limit_window_seconds", 300),
            public_base_url=environ.get("CLAIMLENS_PUBLIC_BASE_URL")
            or _optional_string(web.get("public_base_url")),
            secure_cookies=_bool_setting(environ, web, "CLAIMLENS_SECURE_COOKIES", False),
            registration_enabled=_bool_setting(
                environ,
                web,
                "CLAIMLENS_REGISTRATION_ENABLED",
                False,
            ),
            allow_server_api_key_fallback=_bool_setting(
                environ,
                web,
                "CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK",
                True,
            ),
            key_encryption_secret=environ.get("CLAIMLENS_KEY_ENCRYPTION_SECRET"),
            kapsule_database=_optional_env_path(environ, "CLAIMLENS_KAPSULE_DB"),
        ),
        sources=SourceConfig(
            advanced_source_verification=bool(sources.get("advanced_source_verification", False)),
            enable_pubmed=bool(sources.get("enable_pubmed", True)),
            enable_semantic_scholar=bool(sources.get("enable_semantic_scholar", True)),
            enable_web_search=bool(sources.get("enable_web_search", False)),
        ),
        api_keys=ApiKeys(
            youtube=environ.get("YOUTUBE_API_KEY"),
            openai=environ.get("OPENAI_API_KEY"),
            semantic_scholar=environ.get("SEMANTIC_SCHOLAR_API_KEY"),
            ncbi=environ.get("NCBI_API_KEY"),
        ),
    )


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as file:
        return tomllib.load(file)


def _optional_env_path(env: dict[str, str], key: str) -> Path | None:
    value = env.get(key)
    return Path(value).expanduser() if value else None


def _env_path(env: dict[str, str], key: str, fallback: str | Path) -> Path:
    return _path(env.get(key, fallback))


def _path(value: str | Path) -> Path:
    return Path(value).expanduser()


def _config_path(value: str | Path, *, base: Path | None) -> Path:
    path = _path(value)
    if base is not None and not path.is_absolute():
        return base / path
    return path


def _int_setting(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid integer config value for pipeline.{key}: {value!r}") from exc


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _provider_order(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, list | tuple):
        parts = [str(part) for part in value]
    else:
        raise ConfigError(f"Invalid transcripts.provider_order: {value!r}")
    providers = tuple(part.strip().lower() for part in parts if part.strip())
    allowed = {"youtube", "supadata"}
    invalid = sorted(set(providers) - allowed)
    if invalid:
        raise ConfigError(f"Unsupported transcript provider(s): {', '.join(invalid)}")
    return providers or ("youtube",)


def _bool_setting(
    env: dict[str, str],
    values: dict[str, Any],
    env_key: str,
    default: bool,
) -> bool:
    raw = env.get(env_key, values.get(_toml_bool_key(env_key), default))
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Invalid boolean config value for {env_key}: {raw!r}")


def _toml_bool_key(env_key: str) -> str:
    return env_key.removeprefix("CLAIMLENS_").lower()
