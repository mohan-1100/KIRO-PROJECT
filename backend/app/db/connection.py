"""
Database connection module for ImpactLens.

Uses SQLite via Python's built-in sqlite3. The database file path is
read from the DATABASE_URL environment variable (strip the sqlite:///
prefix to get the file path). Falls back to ./impactlens.db if the
env var is not set.

PRAGMA foreign_keys = ON is enabled on every connection to enforce
referential integrity between scenarios, components, edges, and
simulation_history tables.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv

load_dotenv()


def _get_db_path() -> str:
    """Derive the SQLite file path from DATABASE_URL env var."""
    url = os.getenv("DATABASE_URL", "sqlite:///./impactlens.db")
    # Strip the sqlite:/// prefix
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    return url


def get_db_connection() -> sqlite3.Connection:
    """
    Open and return a SQLite connection with:
    - Row factory set to sqlite3.Row (allows column access by name)
    - PRAGMA foreign_keys = ON (enforces FK constraints)
    - PRAGMA journal_mode = WAL (better concurrent read performance)

    Caller is responsible for calling .close() or using get_db() context manager.
    """
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Usage:
        with get_db() as db:
            rows = db.execute("SELECT * FROM scenarios").fetchall()

    Automatically commits on success, rolls back on exception, and
    always closes the connection.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_path_for_testing() -> str:
    """Expose the resolved DB path (used by test fixtures)."""
    return _get_db_path()
