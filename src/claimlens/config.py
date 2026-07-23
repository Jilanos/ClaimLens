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


@dataclass(frozen=True)
class SourceConfig:
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
    sources: SourceConfig
    api_keys: ApiKeys


DEFAULT_CONFIG_PATH = Path("config/claimlens.example.toml")


class ConfigError(ValueError):
    """Raised when local ClaimLens configuration is invalid."""


def load_config(
    config_path: Path | str | None = None,
    *,
    env: dict[str, str] | None = None,
) -> AppConfig:
    """Load config from TOML plus environment variables."""

    environ = os.environ if env is None else env
    repo_root = Path.cwd()
    raw = _read_toml(Path(config_path) if config_path else repo_root / DEFAULT_CONFIG_PATH)

    paths = raw.get("paths", {})
    pipeline = raw.get("pipeline", {})
    sources = raw.get("sources", {})

    database = _env_path(environ, "CLAIMLENS_DB", paths.get("database", "data/claimlens.sqlite3"))
    outputs = _env_path(environ, "CLAIMLENS_OUTPUTS", paths.get("outputs", "outputs"))
    transcripts = _env_path(
        environ,
        "CLAIMLENS_TRANSCRIPTS",
        paths.get("transcripts", "outputs/transcripts"),
    )
    briefs = _env_path(environ, "CLAIMLENS_BRIEFS", paths.get("briefs", "outputs/briefs"))

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
        ),
        sources=SourceConfig(
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


def _env_path(env: dict[str, str], key: str, fallback: str | Path) -> Path:
    return _path(env.get(key, fallback))


def _path(value: str | Path) -> Path:
    return Path(value).expanduser()


def _int_setting(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid integer config value for pipeline.{key}: {value!r}") from exc
