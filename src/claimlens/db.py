"""SQLite storage for ClaimLens."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Protocol

SCHEMA_VERSION = 3

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
    adapter TEXT,
    external_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
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

CREATE TABLE IF NOT EXISTS verification_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    summary_id INTEGER NOT NULL REFERENCES summaries(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    source_adapters_json TEXT NOT NULL DEFAULT '[]',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    failure_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_verification_runs_video_id
ON verification_runs(video_id);
CREATE INDEX IF NOT EXISTS idx_verification_runs_summary_id
ON verification_runs(summary_id);
CREATE INDEX IF NOT EXISTS idx_verification_runs_status
ON verification_runs(status);

CREATE TABLE IF NOT EXISTS evidence_snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_run_id INTEGER NOT NULL REFERENCES verification_runs(id) ON DELETE CASCADE,
    claim_id INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    polarity TEXT NOT NULL CHECK (polarity IN ('supports', 'contradicts', 'context')),
    snippet TEXT NOT NULL,
    rationale TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_snippets_verification_run_id
ON evidence_snippets(verification_run_id);
CREATE INDEX IF NOT EXISTS idx_evidence_snippets_claim_id
ON evidence_snippets(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_snippets_source_id
ON evidence_snippets(source_id);

CREATE TABLE IF NOT EXISTS brief_artifacts (
    video_id TEXT PRIMARY KEY REFERENCES videos(id) ON DELETE CASCADE,
    summary_id INTEGER NOT NULL REFERENCES summaries(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    source_verification_status TEXT NOT NULL DEFAULT 'not_advanced_source_verified',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_metadata (key, value)
VALUES ('schema_version', '3')
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
    _add_column_if_missing(connection, "sources", "adapter", "TEXT")
    _add_column_if_missing(connection, "sources", "external_id", "TEXT")
    _add_column_if_missing(
        connection,
        "sources",
        "metadata_json",
        "TEXT NOT NULL DEFAULT '{}'",
    )


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
    steps = ["captions", "clean_transcript", "analysis", "brief", "source_verification"]
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
                WHEN 'source_verification' THEN 5
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


def create_verification_run(
    database_path: Path | str,
    *,
    video_id: str,
    summary_id: int,
    adapters: list[str],
) -> int:
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO verification_runs
                    (video_id, summary_id, status, source_adapters_json)
                VALUES (?, ?, 'running', ?)
                """,
                (video_id, summary_id, json.dumps(adapters)),
            )
    return int(cursor.lastrowid)


def finish_verification_run(
    database_path: Path | str,
    *,
    verification_run_id: int,
    status: str,
    failure_message: str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                UPDATE verification_runs
                SET status = ?,
                    failure_message = ?,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, failure_message, verification_run_id),
            )


def latest_verification_run(database_path: Path | str, video_id: str) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT * FROM verification_runs
            WHERE video_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (video_id,),
        ).fetchone()


def upsert_source(
    database_path: Path | str,
    *,
    title: str,
    url: str,
    publisher: str | None,
    published_at: str | None,
    abstract_or_snippet: str | None,
    adapter: str,
    external_id: str | None = None,
    metadata: dict | None = None,
) -> int:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO sources
                    (title, url, publisher, published_at, abstract_or_snippet,
                     adapter, external_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    publisher = excluded.publisher,
                    published_at = excluded.published_at,
                    abstract_or_snippet = excluded.abstract_or_snippet,
                    adapter = excluded.adapter,
                    external_id = excluded.external_id,
                    metadata_json = excluded.metadata_json,
                    retrieved_at = CURRENT_TIMESTAMP
                """,
                (
                    title,
                    url,
                    publisher,
                    published_at,
                    abstract_or_snippet,
                    adapter,
                    external_id,
                    json.dumps(metadata or {}),
                ),
            )
            row = connection.execute(
                "SELECT id FROM sources WHERE url = ?",
                (url,),
            ).fetchone()
    return int(row["id"])


def link_claim_source(
    database_path: Path | str,
    *,
    claim_id: int,
    source_id: int,
    relevance: str = "candidate",
    notes: str | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO claim_sources (claim_id, source_id, relevance, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(claim_id, source_id) DO UPDATE SET
                    relevance = excluded.relevance,
                    notes = excluded.notes
                """,
                (claim_id, source_id, relevance, notes),
            )


def insert_evidence_snippet(
    database_path: Path | str,
    *,
    verification_run_id: int,
    claim_id: int,
    source_id: int,
    polarity: str,
    snippet: str,
    rationale: str | None = None,
) -> int:
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO evidence_snippets
                    (verification_run_id, claim_id, source_id, polarity, snippet, rationale)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (verification_run_id, claim_id, source_id, polarity, snippet, rationale),
            )
    return int(cursor.lastrowid)


def update_claim_verdict(
    database_path: Path | str,
    *,
    claim_id: int,
    verdict: str,
    rationale: str,
    confidence: float | None = None,
) -> None:
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                UPDATE claims
                SET verdict = ?,
                    rationale = ?,
                    confidence = ?
                WHERE id = ?
                """,
                (verdict, rationale, confidence, claim_id),
            )


def sources_for_claim(database_path: Path | str, claim_id: int) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT sources.*, claim_sources.relevance, claim_sources.notes
            FROM sources
            INNER JOIN claim_sources ON claim_sources.source_id = sources.id
            WHERE claim_sources.claim_id = ?
            ORDER BY sources.id
            """,
            (claim_id,),
        ).fetchall()


def evidence_for_verification(
    database_path: Path | str,
    verification_run_id: int,
) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT
                evidence_snippets.*,
                claims.claim,
                claims.verdict,
                sources.title AS source_title,
                sources.url AS source_url,
                sources.publisher AS source_publisher,
                sources.published_at AS source_published_at,
                sources.adapter AS source_adapter
            FROM evidence_snippets
            INNER JOIN claims ON claims.id = evidence_snippets.claim_id
            INNER JOIN sources ON sources.id = evidence_snippets.source_id
            WHERE evidence_snippets.verification_run_id = ?
            ORDER BY claims.id, evidence_snippets.id
            """,
            (verification_run_id,),
        ).fetchall()


def verified_claims_for_summary(
    database_path: Path | str,
    summary_id: int,
) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT *
            FROM claims
            WHERE summary_id = ?
            ORDER BY id
            """,
            (summary_id,),
        ).fetchall()
