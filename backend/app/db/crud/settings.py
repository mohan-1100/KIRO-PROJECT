"""
CRUD helpers for the settings table.

Key-value store for application configuration.
The initial version stores only freshness_threshold_hours (default: 72).
"""

import sqlite3
from typing import Optional


def get_setting(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """Return the value for a settings key, or None if not found."""
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Upsert a settings value."""
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()


def get_freshness_threshold(conn: sqlite3.Connection) -> int:
    """Return the freshness threshold in hours. Defaults to 72 if not set."""
    value = get_setting(conn, "freshness_threshold_hours")
    return int(value) if value is not None else 72


def set_freshness_threshold(conn: sqlite3.Connection, hours: int) -> None:
    """Set the freshness threshold in hours (must be 1–8760)."""
    if not (1 <= hours <= 8760):
        raise ValueError(f"freshness_threshold_hours must be between 1 and 8760, got {hours}")
    set_setting(conn, "freshness_threshold_hours", str(hours))


def get_all_settings(conn: sqlite3.Connection) -> dict[str, str]:
    """Return all settings as a dict."""
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}
