"""
CRUD helpers for the scenarios table.

Scenarios are the top-level grouping for components and edges.
Each scenario maintains its own baseline graph and health states.
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_scenario(
    conn: sqlite3.Connection,
    name: str,
    description: Optional[str] = None,
) -> dict:
    """
    Insert a new scenario. Returns the created row as a dict.
    Raises sqlite3.IntegrityError on duplicate name (enforced by UNIQUE constraint).
    """
    scenario_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO scenarios (id, name, description, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (scenario_id, name, description, now),
    )
    conn.commit()
    return get_scenario(conn, scenario_id)  # type: ignore[return-value]


def get_scenario(conn: sqlite3.Connection, scenario_id: str) -> Optional[dict]:
    """Return a single scenario by ID, or None if not found."""
    row = conn.execute(
        "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_scenario_by_name(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    """Return a scenario by name (case-insensitive), or None if not found."""
    row = conn.execute(
        "SELECT * FROM scenarios WHERE lower(name) = lower(?)", (name,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_scenarios(conn: sqlite3.Connection) -> list[dict]:
    """Return all scenarios ordered by created_at ascending."""
    rows = conn.execute(
        "SELECT * FROM scenarios ORDER BY created_at ASC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_scenario(conn: sqlite3.Connection, scenario_id: str) -> bool:
    """
    Delete a scenario and all its components, edges, and simulation_history
    via CASCADE. Returns True if a row was deleted, False if not found.
    """
    cursor = conn.execute(
        "DELETE FROM scenarios WHERE id = ?", (scenario_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


def scenario_exists(conn: sqlite3.Connection, scenario_id: str) -> bool:
    """Return True if a scenario with this ID exists."""
    row = conn.execute(
        "SELECT 1 FROM scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()
    return row is not None
