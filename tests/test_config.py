from pathlib import Path

import pytest

from claimlens.config import ConfigError, load_config


def test_load_config_uses_defaults_without_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.paths.database == Path("data/claimlens.sqlite3")
    assert config.pipeline.max_videos_per_channel == 10
    assert config.sources.advanced_source_verification is False
    assert config.sources.enable_pubmed is True
    assert config.api_keys.openai is None


def test_load_config_reads_env_and_toml(tmp_path, monkeypatch):
    config_file = tmp_path / "claimlens.toml"
    config_file.write_text(
        """
[paths]
database = "custom/claimlens.sqlite3"

[pipeline]
max_videos_per_channel = 3
candidate_min_duration_seconds = 120

[sources]
advanced_source_verification = true
enable_pubmed = false
enable_semantic_scholar = true
enable_web_search = true
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("CLAIMLENS_DB", "override.sqlite3")
    monkeypatch.setenv("CLAIMLENS_OUTPUTS", "env/outputs")
    monkeypatch.setenv("CLAIMLENS_TRANSCRIPTS", "env/transcripts")
    monkeypatch.setenv("CLAIMLENS_BRIEFS", "env/briefs")

    config = load_config(config_file)

    assert config.paths.database == Path("override.sqlite3")
    assert config.paths.outputs == Path("env/outputs")
    assert config.paths.transcripts == Path("env/transcripts")
    assert config.paths.briefs == Path("env/briefs")
    assert config.pipeline.max_videos_per_channel == 3
    assert config.pipeline.candidate_min_duration_seconds == 120
    assert config.sources.advanced_source_verification is True
    assert config.sources.enable_pubmed is False
    assert config.sources.enable_web_search is True
    assert config.api_keys.openai == "test-openai-key"


def test_load_config_reports_invalid_integer_values(tmp_path):
    config_file = tmp_path / "claimlens.toml"
    config_file.write_text(
        """
[pipeline]
max_videos_per_channel = "many"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigError,
        match="Invalid integer config value for pipeline.max_videos_per_channel",
    ):
        load_config(config_file)
