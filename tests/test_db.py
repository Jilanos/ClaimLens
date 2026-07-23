import sqlite3
from unittest.mock import MagicMock

from claimlens import db
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
