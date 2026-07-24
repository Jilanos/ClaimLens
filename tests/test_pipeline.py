import sqlite3

import pytest

from claimlens import db
from claimlens.api_keys import save_supadata_api_key
from claimlens.config import load_config
from claimlens.pipeline import (
    PipelineError,
    add_manual_transcript,
    clean_run_transcript,
    clean_transcript_text,
    create_run,
    extract_required_subtitles,
    parse_youtube_video_url,
)
from claimlens.youtube import (
    SupadataQuotaError,
    TranscriptResult,
    TranscriptSegment,
    YouTubeError,
    YouTubeVideo,
)


def test_parse_youtube_video_url_formats():
    assert parse_youtube_video_url("https://www.youtube.com/watch?v=abc123XYZ_").video_id == (
        "abc123XYZ_"
    )
    assert parse_youtube_video_url("https://youtu.be/abc123XYZ_?si=1").video_id == "abc123XYZ_"
    assert parse_youtube_video_url("https://www.youtube.com/shorts/abc123XYZ_").video_id == (
        "abc123XYZ_"
    )


def test_parse_youtube_video_url_rejects_channel():
    with pytest.raises(PipelineError, match="exactly one YouTube video ID"):
        parse_youtube_video_url("https://www.youtube.com/@example/videos")


def test_create_run_records_video_and_steps(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")

    run = db.get_pipeline_run(database, run_id)
    steps = db.list_run_steps(database, run_id)
    assert run["video_id"] == "abc123XYZ_"
    assert run["source_url"] == "https://www.youtube.com/watch?v=abc123XYZ_"
    assert [step["step"] for step in steps] == [
        "captions",
        "clean_transcript",
        "analysis",
        "brief",
        "source_verification",
    ]


def test_create_run_can_fetch_video_metadata(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    monkeypatch.setattr(
        "claimlens.pipeline.fetch_video_metadata",
        lambda url: YouTubeVideo(id="abc123XYZ_", title="Real title", url=url),
    )

    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        fetch_metadata=True,
    )
    run = db.get_pipeline_run(database, run_id)
    video = db.get_video(database, run["video_id"])

    assert video["title"] == "Real title"


def test_extract_required_subtitles_persists_failure(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")

    def fail(video_id):
        raise RuntimeError("no captions")

    monkeypatch.setattr("claimlens.pipeline.fetch_transcript", fail)

    with pytest.raises(YouTubeError, match="Subtitles are unavailable"):
        extract_required_subtitles(database, run_id)

    run = db.get_pipeline_run(database, run_id)
    steps = {step["step"]: step for step in db.list_run_steps(database, run_id)}
    assert run["status"] == "failed"
    assert "Subtitles are unavailable" in steps["captions"]["failure_message"]


def test_clean_transcript_text_removes_timestamps_noise_and_duplicates():
    cleaned = clean_transcript_text(
        """
        00:00 hello there
        [Music]
        00:01 hello there
        1:02:03 important claim
        """
    )

    assert "00:00" not in cleaned
    assert "[Music]" not in cleaned
    assert cleaned.splitlines() == ["hello there", "important claim"]


def test_clean_run_transcript_writes_artifact_and_keeps_raw_segments(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    monkeypatch.setattr(
        "claimlens.pipeline.fetch_transcript",
        lambda video_id: TranscriptResult(
            video_id=video_id,
            source="youtube",
            language="en",
            text="00:00 hello\n00:01 world",
            segments=[
                TranscriptSegment(start_seconds=0.0, end_seconds=1.0, text="00:00 hello"),
                TranscriptSegment(start_seconds=1.0, end_seconds=2.0, text="00:01 world"),
            ],
        ),
    )

    extract_required_subtitles(database, run_id)
    output_path = clean_run_transcript(database, run_id, outputs_path=tmp_path / "transcripts")

    cleaned = db.get_cleaned_transcript(database, "abc123XYZ_")
    with sqlite3.connect(database) as connection:
        raw_count = connection.execute("SELECT COUNT(*) FROM transcript_segments").fetchone()[0]
    assert output_path.read_text(encoding="utf-8") == "hello\nworld\n"
    assert cleaned["text"] == "hello\nworld"
    assert raw_count == 2


def test_manual_transcript_fallback_continues_pipeline(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")

    transcript_id = add_manual_transcript(
        database,
        run_id,
        text="00:00 pasted transcript",
        language="en",
        guest_token="guest123",
    )
    output_path = clean_run_transcript(database, run_id, outputs_path=tmp_path / "transcripts")

    transcript = db.latest_transcript(database, "abc123XYZ_")
    assert transcript["id"] == transcript_id
    assert transcript["source"] == "user_paste"
    assert transcript["submitted_by_guest_token"] == "guest123"
    assert output_path.read_text(encoding="utf-8") == "pasted transcript\n"


def test_supadata_rotation_retries_next_key(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="first",
        value="first-key",
        priority=10,
        deployment_secret="deploy-secret",
    )
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="second",
        value="second-key",
        priority=20,
        deployment_secret="deploy-secret",
    )
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        user_id=user_id,
    )
    calls = []

    class Client:
        def __init__(self, *, api_key, timeout):
            self.api_key = api_key
            calls.append(("init", api_key, timeout))

        def fetch_native_transcript(self, *, video_url, video_id, language):
            calls.append((self.api_key, video_url, language))
            if self.api_key == "first-key":
                raise SupadataQuotaError("limit", status_code=429)
            return TranscriptResult(
                video_id=video_id,
                source="supadata-native",
                language=language or "en",
                text="native transcript",
                segments=[TranscriptSegment(0.0, 1.0, "native transcript")],
            )

    monkeypatch.setattr("claimlens.pipeline.SupadataClient", Client)
    config = load_config(
        env={
            "CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret",
            "CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER": "supadata",
        }
    )

    transcript = extract_required_subtitles(database, run_id, config=config, user_id=user_id)
    rows = db.list_supadata_api_keys(database, user_id=user_id)

    assert transcript.source == "supadata-native"
    assert [call[0] for call in calls] == ["init", "first-key", "init", "second-key"]
    assert [call[2] for call in calls if call[0] == "init"] == [10, 10]
    assert rows[0]["status"] == "exhausted"
    assert rows[1]["last_used_at"] is not None


def test_supadata_locally_exhausted_key_is_skipped(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="spent",
        value="spent-key",
        priority=10,
        deployment_secret="deploy-secret",
    )
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_", user_id=user_id)

    row = db.list_supadata_api_keys(database, user_id=user_id)[0]
    db.mark_supadata_api_key_exhausted(
        database,
        user_id=user_id,
        key_id=row["id"],
        exhausted_until="2099-01-01 00:00:00",
        last_error="already exhausted",
    )

    class Client:
        def __init__(self, **kwargs):
            raise AssertionError("locally exhausted key should not create a client")

    monkeypatch.setattr("claimlens.pipeline.SupadataClient", Client)
    config = load_config(
        env={
            "CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret",
            "CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER": "supadata",
        }
    )

    with pytest.raises(YouTubeError, match="pasted transcript fallback"):
        extract_required_subtitles(database, run_id, config=config, user_id=user_id)

    rows = db.list_supadata_api_keys(database, user_id=user_id)
    assert rows[0]["status"] == "exhausted"


def test_supadata_failure_falls_back_to_youtube(monkeypatch, tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="only-key",
        value="only-key",
        priority=10,
        deployment_secret="deploy-secret",
    )
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_", user_id=user_id)

    class Client:
        def __init__(self, *, api_key, timeout):
            assert api_key == "only-key"
            assert timeout == 10

        def fetch_native_transcript(self, **kwargs):
            raise SupadataQuotaError("limit", status_code=429)

    monkeypatch.setattr("claimlens.pipeline.SupadataClient", Client)
    monkeypatch.setattr(
        "claimlens.pipeline.fetch_transcript",
        lambda video_id: TranscriptResult(
            video_id=video_id,
            source="youtube",
            language="en",
            text="fallback transcript",
            segments=[],
        ),
    )
    config = load_config(
        env={
            "CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret",
            "CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER": "supadata,youtube",
        }
    )

    transcript = extract_required_subtitles(database, run_id, config=config, user_id=user_id)

    assert transcript.source == "youtube"
