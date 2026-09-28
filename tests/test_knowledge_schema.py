"""Ensure the proposed SQL schema rejects invalid state and orphan graph edges."""

import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database():
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "schemas/knowledge_schema.sql").read_text())
    yield connection
    connection.close()


def test_orphan_edge_is_rejected(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?, ?, ?)",
            ("e1", "missing", "also_missing", "USES", None, "{}"),
        )


def test_unknown_node_type_is_rejected(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            "INSERT INTO nodes VALUES (?, ?, ?, ?)", ("n1", "UntrustedType", "example", "{}")
        )


def test_schema_can_be_applied_idempotently(database):
    database.executescript((ROOT / "schemas/knowledge_schema.sql").read_text())
    assert database.execute("PRAGMA foreign_keys").fetchone() == (1,)
