"""SQLite storage for ClaimLens."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Protocol

SCHEMA_VERSION = 2

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    published_at TEXT,
    duration_seconds INTEGER,
    view_count INTEGER,
    like_count INTEGER,
    processing_status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_processing_status ON videos(processing_status);
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_command ON pipeline_runs(command);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);

CREATE TABLE IF NOT EXISTS run_steps (
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    failure_message TEXT,
    output_path TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, step)
);

CREATE INDEX IF NOT EXISTS idx_run_steps_status ON run_steps(status);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    language TEXT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, source)
);

CREATE INDEX IF NOT EXISTS idx_transcripts_video_id ON transcripts(video_id);

CREATE TABLE IF NOT EXISTS transcript_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    start_seconds REAL NOT NULL,
    end_seconds REAL,
    text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transcript_segments_transcript_id
ON transcript_segments(transcript_id);

CREATE TABLE IF NOT EXISTS cleaned_transcripts (
    video_id TEXT PRIMARY KEY REFERENCES videos(id) ON DELETE CASCADE,
    transcript_id INTEGER NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    output_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    model TEXT,
    summary TEXT NOT NULL,
    key_points_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_summaries_video_id ON summaries(video_id);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    summary_id INTEGER REFERENCES summaries(id) ON DELETE SET NULL,
    claim TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT 'general',
    verifiability TEXT NOT NULL DEFAULT 'unknown',
    verdict TEXT NOT NULL DEFAULT 'not_checked',
    confidence REAL,
    rationale TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claims_video_id ON claims(video_id);
CREATE INDEX IF NOT EXISTS idx_claims_domain ON claims(domain);
CREATE INDEX IF NOT EXISTS idx_claims_verdict ON claims(verdict);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    publisher TEXT,
    published_at TEXT,
    abstract_or_snippet TEXT,
    retrieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sources_publisher ON sources(publisher);
CREATE INDEX IF NOT EXISTS idx_sources_published_at ON sources(published_at);

CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    relevance TEXT NOT NULL DEFAULT 'candidate',
    notes TEXT,
    PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS brief_artifacts (
    video_id TEXT PRIMARY KEY REFERENCES videos(id) ON DELETE CASCADE,
    summary_id INTEGER NOT NULL REFERENCES summaries(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    source_verification_status TEXT NOT NULL DEFAULT 'not_advanced_source_verified',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_metadata (key, value)
VALUES ('schema_version', '2')
ON CONFLICT(key) DO UPDATE SET
    value = excluded.value,
    updated_at = CURRENT_TIMESTAMP;
"""


class VideoLike(Protocol):
    id: str
    title: str
    url: str
    published_text: str | None


class TranscriptLike(Protocol):
    video_id: str
    source: str
    language: str
    text: str
    segments: list


def connect(database_path: Path | str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db(database_path: Path | str) -> Path:
    path = Path(database_path)
    with closing(connect(path)) as connection:
        with connection:
            connection.executescript(SCHEMA_SQL)
            _migrate_schema(connection)
    return path


def _migrate_schema(connection: sqlite3.Connection) -> None:
    _add_column_if_missing(connection, "pipeline_runs", "video_id", "TEXT")
    _add_column_if_missing(connection, "pipeline_runs", "source_url", "TEXT")
    _add_column_if_missing(connection, "pipeline_runs", "current_step", "TEXT")
    _add_column_if_missing(connection, "pipeline_runs", "failure_message", "TEXT")


def _add_column_if_missing(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def table_names(database_path: Path | str) -> set[str]:
    with closing(connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    return {row["name"] for row in rows}


def upsert_channel(
    database_path: Path | str,
    *,
    channel_id: str,
    title: str | None = None,
    url: str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO channels (id, title, url)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = COALESCE(excluded.title, channels.title),
                    url = COALESCE(excluded.url, channels.url),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (channel_id, title, url),
            )


def upsert_video(database_path: Path | str, *, channel_id: str, video: VideoLike) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO videos (id, channel_id, title, url, published_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    title = excluded.title,
                    url = excluded.url,
                    published_at = COALESCE(excluded.published_at, videos.published_at),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (video.id, channel_id, video.title, video.url, video.published_text),
            )


def upsert_transcript(database_path: Path | str, transcript: TranscriptLike) -> int:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO transcripts (video_id, source, language, text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(video_id, source) DO UPDATE SET
                    language = excluded.language,
                    text = excluded.text,
                    created_at = CURRENT_TIMESTAMP
                """,
                (
                    transcript.video_id,
                    transcript.source,
                    transcript.language,
                    transcript.text,
                ),
            )
            transcript_id = connection.execute(
                "SELECT id FROM transcripts WHERE video_id = ? AND source = ?",
                (transcript.video_id, transcript.source),
            ).fetchone()["id"]
            connection.execute(
                "DELETE FROM transcript_segments WHERE transcript_id = ?",
                (transcript_id,),
            )
            connection.executemany(
                """
                INSERT INTO transcript_segments (transcript_id, start_seconds, end_seconds, text)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        transcript_id,
                        segment.start_seconds,
                        segment.end_seconds,
                        segment.text,
                    )
                    for segment in transcript.segments
                ],
            )
    return int(transcript_id)


def create_pipeline_run(
    database_path: Path | str,
    *,
    video_id: str,
    source_url: str,
    command: str = "run-video",
) -> int:
    steps = ["captions", "clean_transcript", "analysis", "brief"]
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO pipeline_runs
                    (command, status, video_id, source_url, current_step, details)
                VALUES (?, 'created', ?, ?, 'captions', ?)
                """,
                (
                    command,
                    video_id,
                    source_url,
                    json.dumps({"video_id": video_id, "source_url": source_url}),
                ),
            )
            run_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO run_steps (run_id, step, status)
                VALUES (?, ?, 'pending')
                """,
                [(run_id, step) for step in steps],
            )
    return run_id


def set_run_status(
    database_path: Path | str,
    *,
    run_id: int,
    status: str,
    current_step: str | None = None,
    failure_message: str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                UPDATE pipeline_runs
                SET status = ?,
                    current_step = COALESCE(?, current_step),
                    failure_message = ?,
                    finished_at = CASE
                        WHEN ? IN ('failed', 'succeeded') THEN CURRENT_TIMESTAMP
                        ELSE finished_at
                    END
                WHERE id = ?
                """,
                (status, current_step, failure_message, status, run_id),
            )


def set_step_status(
    database_path: Path | str,
    *,
    run_id: int,
    step: str,
    status: str,
    failure_message: str | None = None,
    output_path: str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO run_steps (run_id, step, status, failure_message, output_path)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id, step) DO UPDATE SET
                    status = excluded.status,
                    failure_message = excluded.failure_message,
                    output_path = COALESCE(excluded.output_path, run_steps.output_path),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (run_id, step, status, failure_message, output_path),
            )


def get_pipeline_run(database_path: Path | str, run_id: int) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT * FROM pipeline_runs WHERE id = ?",
            (run_id,),
        ).fetchone()


def latest_pipeline_run_for_video(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM pipeline_runs
            WHERE video_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (video_id,),
        ).fetchone()


def list_pipeline_runs(database_path: Path | str) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT * FROM pipeline_runs ORDER BY id DESC",
        ).fetchall()


def list_run_steps(database_path: Path | str, run_id: int) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM run_steps
            WHERE run_id = ?
            ORDER BY CASE step
                WHEN 'captions' THEN 1
                WHEN 'clean_transcript' THEN 2
                WHEN 'analysis' THEN 3
                WHEN 'brief' THEN 4
                ELSE 99
            END
            """,
            (run_id,),
        ).fetchall()


def latest_transcript(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM transcripts
            WHERE video_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (video_id,),
        ).fetchone()


def get_transcript_segments(database_path: Path | str, transcript_id: int) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM transcript_segments
            WHERE transcript_id = ?
            ORDER BY start_seconds, id
            """,
            (transcript_id,),
        ).fetchall()


def upsert_cleaned_transcript(
    database_path: Path | str,
    *,
    video_id: str,
    transcript_id: int,
    text: str,
    output_path: Path | str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO cleaned_transcripts (video_id, transcript_id, text, output_path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    transcript_id = excluded.transcript_id,
                    text = excluded.text,
                    output_path = excluded.output_path,
                    created_at = CURRENT_TIMESTAMP
                """,
                (video_id, transcript_id, text, str(output_path) if output_path else None),
            )


def get_cleaned_transcript(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT * FROM cleaned_transcripts WHERE video_id = ?",
            (video_id,),
        ).fetchone()


def upsert_analysis(
    database_path: Path | str,
    *,
    video_id: str,
    model: str,
    summary: str,
    key_points: list[str],
    notable_claims: list[str],
    caveats: list[str] | None = None,
    editorial_notes: list[str] | None = None,
) -> int:
    details = {
        "key_points": key_points,
        "caveats": caveats or [],
        "editorial_notes": editorial_notes or [],
        "source_verification_status": "not_advanced_source_verified",
    }
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO summaries (video_id, model, summary, key_points_json)
                VALUES (?, ?, ?, ?)
                """,
                (video_id, model, summary, json.dumps(details)),
            )
            summary_id = int(cursor.lastrowid)
            connection.execute(
                "DELETE FROM claims WHERE video_id = ? AND verdict = 'not_checked'",
                (video_id,),
            )
            connection.executemany(
                """
                INSERT INTO claims (video_id, summary_id, claim, verdict, rationale)
                VALUES (?, ?, ?, 'not_checked', 'Advanced source verification has not run.')
                """,
                [(video_id, summary_id, claim) for claim in notable_claims],
            )
    return summary_id


def latest_analysis(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM summaries
            WHERE video_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (video_id,),
        ).fetchone()


def claims_for_summary(database_path: Path | str, summary_id: int) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT * FROM claims WHERE summary_id = ? ORDER BY id",
            (summary_id,),
        ).fetchall()


def upsert_brief_artifact(
    database_path: Path | str,
    *,
    video_id: str,
    summary_id: int,
    path: Path | str,
    source_verification_status: str = "not_advanced_source_verified",
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO brief_artifacts
                    (video_id, summary_id, path, source_verification_status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    summary_id = excluded.summary_id,
                    path = excluded.path,
                    source_verification_status = excluded.source_verification_status,
                    created_at = CURRENT_TIMESTAMP
                """,
                (video_id, summary_id, str(path), source_verification_status),
            )


def latest_brief_artifact(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT * FROM brief_artifacts WHERE video_id = ?",
            (video_id,),
        ).fetchone()
