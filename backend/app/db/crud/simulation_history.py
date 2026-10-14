"""
CRUD helpers for the simulation_history table.

Each simulation_history record corresponds to one Incident.
Records are retained indefinitely and survive server restarts.
"""

import sqlite3
import json
from typing import Optional


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_simulation_record(
    conn: sqlite3.Connection,
    record_id: str,
    scenario_id: str,
    timestamp: str,
    failed_target_id: str,
    failed_target_type: str,
    failure_type: str,
    directly_affected_count: int,
    transitively_affected_count: int,
    impact_score: int,
    data_confidence_score: int,
    full_report: dict,
    status: str = "open",
) -> dict:
    """Insert a new simulation history record. Returns the created row."""
    conn.execute(
        """
        INSERT INTO simulation_history (
            id, scenario_id, timestamp, failed_target_id, failed_target_type,
            failure_type, directly_affected_count, transitively_affected_count,
            impact_score, data_confidence_score, status, full_report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id, scenario_id, timestamp, failed_target_id, failed_target_type,
            failure_type, directly_affected_count, transitively_affected_count,
            impact_score, data_confidence_score, status,
            json.dumps(full_report),
        ),
    )
    conn.commit()
    return get_simulation_record(conn, record_id)  # type: ignore[return-value]


def get_simulation_record(
    conn: sqlite3.Connection, record_id: str
) -> Optional[dict]:
    """Return a single simulation history record by ID, or None."""
    row = conn.execute(
        "SELECT * FROM simulation_history WHERE id = ?", (record_id,)
    ).fetchone()
    if row is None:
        return None
    result = _row_to_dict(row)
    result["full_report"] = json.loads(result.pop("full_report_json", "{}"))
    return result


def list_simulation_history(
    conn: sqlite3.Connection, scenario_id: str
) -> list[dict]:
    """Return simulation history for a scenario in reverse-chronological order."""
    rows = conn.execute(
        """SELECT * FROM simulation_history
           WHERE scenario_id = ?
           ORDER BY timestamp DESC""",
        (scenario_id,),
    ).fetchall()
    results = []
    for row in rows:
        r = _row_to_dict(row)
        r["full_report"] = json.loads(r.pop("full_report_json", "{}"))
        results.append(r)
    return results


def list_all_incidents(conn: sqlite3.Connection) -> list[dict]:
    """Return all simulation history records across all scenarios, reverse-chronological."""
    rows = conn.execute(
        "SELECT * FROM simulation_history ORDER BY timestamp DESC"
    ).fetchall()
    results = []
    for row in rows:
        r = _row_to_dict(row)
        r["full_report"] = json.loads(r.pop("full_report_json", "{}"))
        results.append(r)
    return results


def update_incident_status(
    conn: sqlite3.Connection, record_id: str, status: str
) -> Optional[dict]:
    """Update the status of a simulation history record. Returns None if not found."""
    cursor = conn.execute(
        "UPDATE simulation_history SET status = ? WHERE id = ?",
        (status, record_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        return None
    return get_simulation_record(conn, record_id)
