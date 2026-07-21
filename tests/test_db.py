import sqlite3

from claimlens.db import init_db, table_names

EXPECTED_TABLES = {
    "schema_metadata",
    "channels",
    "videos",
    "pipeline_runs",
    "transcripts",
    "transcript_segments",
    "summaries",
    "claims",
    "sources",
    "claim_sources",
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

    assert schema_version == "1"
