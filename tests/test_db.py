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

    assert schema_version == "3"


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
