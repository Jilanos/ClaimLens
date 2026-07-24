from pathlib import Path

import pytest

from claimlens.config import ConfigError, load_config


def test_load_config_uses_defaults_without_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.paths.database == Path("data/claimlens.sqlite3")
    assert config.pipeline.max_videos_per_channel == 10
    assert config.pipeline.source_verification_max_results == 5
    assert config.pipeline.source_verification_timeout_seconds == 20
    assert config.transcripts.provider_order == ("youtube",)
    assert config.transcripts.supadata_monthly_request_cap == 100
    assert config.transcripts.supadata_timeout_seconds == 10
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
source_verification_max_results = 7
source_verification_timeout_seconds = 15
analysis_max_chars = 12345
report_language = "fr"

[transcripts]
provider_order = ["supadata", "youtube"]
supadata_monthly_request_cap = 25
supadata_language = "fr"

[web]
max_request_bytes = 8192
rate_limit_actions = 4
rate_limit_window_seconds = 60

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
    assert config.pipeline.source_verification_max_results == 7
    assert config.pipeline.source_verification_timeout_seconds == 15
    assert config.pipeline.analysis_max_chars == 12345
    assert config.pipeline.report_language == "fr"
    assert config.transcripts.provider_order == ("supadata", "youtube")
    assert config.transcripts.supadata_monthly_request_cap == 25
    assert config.transcripts.supadata_language == "fr"
    assert config.web.max_request_bytes == 8192
    assert config.web.rate_limit_actions == 4
    assert config.web.rate_limit_window_seconds == 60
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


def test_load_config_rejects_generated_transcript_provider(tmp_path):
    config_file = tmp_path / "claimlens.toml"
    config_file.write_text(
        """
[transcripts]
provider_order = ["generate"]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Unsupported transcript provider"):
        load_config(config_file)


def test_explicit_config_resolves_relative_paths_from_config_directory(tmp_path, monkeypatch):
    config_file = tmp_path / "deploy" / "claimlens.toml"
    config_file.parent.mkdir()
    config_file.write_text(
        """
[paths]
database = "data/prod.sqlite3"
briefs = "briefs"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = load_config(config_file)

    assert config.paths.database == config_file.parent / "data/prod.sqlite3"
    assert config.paths.briefs == config_file.parent / "briefs"


def test_claimlens_config_env_selects_config_file(tmp_path):
    config_file = tmp_path / "claimlens.toml"
    config_file.write_text(
        """
[pipeline]
report_language = "fr"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(env={"CLAIMLENS_CONFIG": str(config_file)})

    assert config.pipeline.report_language == "fr"


def test_load_config_reads_deployed_provider_order_and_supadata_timeout():
    config = load_config(
        env={
            "CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER": "supadata,youtube",
            "CLAIMLENS_SUPADATA_TIMEOUT_SECONDS": "7",
        }
    )

    assert config.transcripts.provider_order == ("supadata", "youtube")
    assert config.transcripts.supadata_timeout_seconds == 7


def test_load_config_rejects_non_positive_supadata_timeout():
    with pytest.raises(ConfigError, match="supadata_timeout_seconds"):
        load_config(env={"CLAIMLENS_SUPADATA_TIMEOUT_SECONDS": "0"})
