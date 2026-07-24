import sqlite3
from dataclasses import dataclass
from unittest.mock import MagicMock

from claimlens import db
from claimlens.db import init_db, table_names


@dataclass(frozen=True)
class Video:
    id: str
    title: str
    url: str
    published_text: str | None = None


@dataclass(frozen=True)
class Segment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class Transcript:
    video_id: str
    source: str
    language: str
    text: str
    segments: list[Segment]

EXPECTED_TABLES = {
    "schema_metadata",
    "channels",
    "videos",
    "pipeline_runs",
    "run_steps",
    "transcripts",
    "transcript_segments",
    "cleaned_transcripts",
    "summaries",
    "claims",
    "sources",
    "claim_sources",
    "brief_artifacts",
    "verification_runs",
    "evidence_snippets",
    "jobs",
    "users",
    "sessions",
    "user_api_keys",
    "supadata_api_keys",
}


def test_init_db_creates_expected_tables(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    init_db(database)

    assert database.exists()
    assert EXPECTED_TABLES.issubset(table_names(database))


def test_init_db_is_idempotent(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    init_db(database)
    init_db(database)

    with sqlite3.connect(database) as connection:
        schema_version = connection.execute(
            "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
        ).fetchone()[0]

    assert schema_version == "6"


def test_supadata_api_key_pool_tracks_quota_state(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")

    key_id = db.create_supadata_api_key(
        database,
        user_id=user_id,
        label="Free key 1",
        priority=10,
        encrypted_value="encrypted",
        key_fingerprint="fingerprint",
        masked_value="sup...key",
    )
    db.mark_supadata_api_key_used(
        database,
        user_id=user_id,
        key_id=key_id,
        billing_period="2026-07",
    )
    assert len(
        db.list_eligible_supadata_api_keys(
            database,
            user_id=user_id,
            billing_period="2026-07",
            monthly_cap=100,
        )
    ) == 1

    db.mark_supadata_api_key_exhausted(
        database,
        user_id=user_id,
        key_id=key_id,
        exhausted_until="2099-01-01 00:00:00",
        last_error="quota",
        max_credits=100,
        used_credits=100,
    )

    rows = db.list_supadata_api_keys(database, user_id=user_id)
    eligible = db.list_eligible_supadata_api_keys(
        database,
        user_id=user_id,
        billing_period="2026-07",
        monthly_cap=100,
    )
    assert rows[0]["status"] == "exhausted"
    assert rows[0]["used_credits"] == 100
    assert eligible == []


def test_connect_applies_sqlite_concurrency_pragmas(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)

    with db.connect(database) as connection:
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert busy_timeout == 5000
    assert journal_mode == "wal"


def test_init_db_closes_connection(monkeypatch, tmp_path):
    connection = MagicMock()
    monkeypatch.setattr(db, "connect", MagicMock(return_value=connection))

    init_db(tmp_path / "claimlens.sqlite3")

    connection.executescript.assert_called_once_with(db.SCHEMA_SQL)
    connection.close.assert_called_once_with()


def test_table_names_closes_connection(monkeypatch, tmp_path):
    connection = MagicMock()
    connection.execute.return_value.fetchall.return_value = [{"name": "videos"}]
    monkeypatch.setattr(db, "connect", MagicMock(return_value=connection))

    assert table_names(tmp_path / "claimlens.sqlite3") == {"videos"}

    connection.close.assert_called_once_with()


def test_upsert_transcript_stores_text_and_segments(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)
    db.upsert_channel(database, channel_id="channel123", title="Channel")
    db.upsert_video(
        database,
        channel_id="channel123",
        video=Video(
            id="video123",
            title="Video",
            url="https://www.youtube.com/watch?v=video123",
        ),
    )

    db.upsert_transcript(
        database,
        Transcript(
            video_id="video123",
            source="youtube-auto",
            language="en",
            text="hello\nworld",
            segments=[
                Segment(start_seconds=0.0, end_seconds=1.0, text="hello"),
                Segment(start_seconds=1.0, end_seconds=2.0, text="world"),
            ],
        ),
    )

    with sqlite3.connect(database) as connection:
        transcript_count = connection.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0]
        segment_count = connection.execute("SELECT COUNT(*) FROM transcript_segments").fetchone()[0]

    assert transcript_count == 1
    assert segment_count == 2


def test_create_job_rejects_duplicate_running_action(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)
    db.upsert_channel(database, channel_id="manual")
    db.upsert_video(
        database,
        channel_id="manual",
        video=Video(
            id="video123",
            title="Video",
            url="https://www.youtube.com/watch?v=video123",
        ),
    )
    run_id = db.create_pipeline_run(
        database,
        video_id="video123",
        source_url="https://www.youtube.com/watch?v=video123",
    )

    first = db.create_job(database, run_id=run_id, action="analysis")
    second = db.create_job(database, run_id=run_id, action="analysis")
    db.update_job(database, job_id=first, status="succeeded", progress=100)
    third = db.create_job(database, run_id=run_id, action="analysis")

    assert first is not None
    assert second is None
    assert third is not None


def test_recover_orphaned_jobs_makes_restart_work_retryable(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)
    db.upsert_channel(database, channel_id="manual")
    db.upsert_video(
        database,
        channel_id="manual",
        video=Video(
            id="video123",
            title="Video",
            url="https://www.youtube.com/watch?v=video123",
        ),
    )
    run_id = db.create_pipeline_run(
        database,
        video_id="video123",
        source_url="https://www.youtube.com/watch?v=video123",
    )
    job_id = db.create_job(database, run_id=run_id, action="analysis")
    db.update_job(database, job_id=job_id, status="running", progress=5)

    assert db.recover_orphaned_jobs(database) == 1
    recovered = db.latest_jobs_for_run(database, run_id)[0]
    retry = db.create_job(database, run_id=run_id, action="analysis")

    assert recovered["status"] == "interrupted"
    assert "restart" in recovered["message"]
    assert retry is not None


def test_record_rate_limit_event_is_atomic_and_identity_scoped(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    init_db(database)

    assert db.record_rate_limit_event(
        database, identity="user:1", window_seconds=60, max_actions=1
    )
    assert not db.record_rate_limit_event(
        database, identity="user:1", window_seconds=60, max_actions=1
    )
    assert db.record_rate_limit_event(
        database, identity="user:2", window_seconds=60, max_actions=1
    )
