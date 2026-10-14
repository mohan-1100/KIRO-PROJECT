"""
CRUD helpers for the components table.

Components are infrastructure nodes (web apps, APIs, databases, etc.)
scoped to a specific scenario. Name uniqueness within a scenario is
enforced case-insensitively at the application layer.
"""

import sqlite3
import uuid
from typing import Any, Optional


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _check_duplicate_name(
    conn: sqlite3.Connection,
    scenario_id: str,
    name: str,
    exclude_id: Optional[str] = None,
) -> bool:
    """Return True if a component with this name already exists in the scenario."""
    if exclude_id:
        row = conn.execute(
            """SELECT 1 FROM components
               WHERE scenario_id = ? AND lower(name) = lower(?) AND id != ?""",
            (scenario_id, name, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT 1 FROM components
               WHERE scenario_id = ? AND lower(name) = lower(?)""",
            (scenario_id, name),
        ).fetchone()
    return row is not None


def create_component(
    conn: sqlite3.Connection,
    scenario_id: str,
    name: str,
    component_type: str,
    criticality: str,
    health_status: str = "unknown",
    last_observed_at: Optional[str] = None,
    evidence_source: str = "unknown",
    confirmation_status: str = "unknown",
    data_quality_score: int = 50,
) -> dict:
    """
    Insert a new component. Raises ValueError on duplicate name (case-insensitive).
    """
    if _check_duplicate_name(conn, scenario_id, name):
        raise ValueError(f"Component name '{name}' already exists in scenario '{scenario_id}'")

    component_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO components (
            id, scenario_id, name, type, criticality, health_status,
            last_observed_at, evidence_source, confirmation_status, data_quality_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            component_id, scenario_id, name, component_type, criticality,
            health_status, last_observed_at, evidence_source,
            confirmation_status, data_quality_score,
        ),
    )
    conn.commit()
    return get_component(conn, scenario_id, component_id)  # type: ignore[return-value]


def get_component(
    conn: sqlite3.Connection, scenario_id: str, component_id: str
) -> Optional[dict]:
    """Return a single component by ID within a scenario, or None."""
    row = conn.execute(
        "SELECT * FROM components WHERE id = ? AND scenario_id = ?",
        (component_id, scenario_id),
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_component_by_id(conn: sqlite3.Connection, component_id: str) -> Optional[dict]:
    """Return a component by ID regardless of scenario (used for cross-scenario validation)."""
    row = conn.execute(
        "SELECT * FROM components WHERE id = ?", (component_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_components(conn: sqlite3.Connection, scenario_id: str) -> list[dict]:
    """Return all components for a scenario."""
    rows = conn.execute(
        "SELECT * FROM components WHERE scenario_id = ? ORDER BY name ASC",
        (scenario_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_component(
    conn: sqlite3.Connection,
    scenario_id: str,
    component_id: str,
    **fields: Any,
) -> Optional[dict]:
    """
    Update specified fields on a component.
    Raises ValueError on duplicate name (case-insensitive).
    Returns None if component not found.
    """
    if "name" in fields:
        if _check_duplicate_name(conn, scenario_id, fields["name"], exclude_id=component_id):
            raise ValueError(
                f"Component name '{fields['name']}' already exists in scenario '{scenario_id}'"
            )

    allowed = {
        "name", "type", "criticality", "health_status",
        "last_observed_at", "evidence_source", "confirmation_status", "data_quality_score",
    }
    update_fields = {k: v for k, v in fields.items() if k in allowed}
    if not update_fields:
        return get_component(conn, scenario_id, component_id)

    set_clause = ", ".join(f"{k} = ?" for k in update_fields)
    values = list(update_fields.values()) + [component_id, scenario_id]
    conn.execute(
        f"UPDATE components SET {set_clause} WHERE id = ? AND scenario_id = ?",
        values,
    )
    conn.commit()
    return get_component(conn, scenario_id, component_id)


def delete_component(
    conn: sqlite3.Connection, scenario_id: str, component_id: str
) -> tuple[bool, list[str]]:
    """
    Delete a component if it has no associated edges.
    Returns (True, []) on success.
    Returns (False, [edge_id, ...]) if edges exist (cannot delete).
    """
    edge_rows = conn.execute(
        """SELECT id FROM edges
           WHERE (source_component_id = ? OR target_component_id = ?)
             AND scenario_id = ?""",
        (component_id, component_id, scenario_id),
    ).fetchall()

    if edge_rows:
        edge_ids = [r["id"] for r in edge_rows]
        return False, edge_ids

    cursor = conn.execute(
        "DELETE FROM components WHERE id = ? AND scenario_id = ?",
        (component_id, scenario_id),
    )
    conn.commit()
    return cursor.rowcount > 0, []
