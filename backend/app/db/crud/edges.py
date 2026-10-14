"""
CRUD helpers for the edges table.

Edges represent directed dependency relationships: A -> B means B depends on A.
If A fails, B may be affected. Edges are scoped to a scenario.

Cross-scenario validation: both source and target components must belong to the
same scenario as the edge. This is enforced at the application layer.
"""

import sqlite3
import uuid
from typing import Any, Optional


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_edge(
    conn: sqlite3.Connection,
    scenario_id: str,
    source_component_id: str,
    target_component_id: str,
    label: Optional[str] = None,
    evidence_source: str = "unknown",
    confirmation_status: str = "unknown",
    last_observed_at: Optional[str] = None,
) -> dict:
    """
    Insert a new directed edge.

    Raises:
        ValueError: self-loop (source == target)
        ValueError: cross-scenario (source or target not in scenario_id)
        sqlite3.IntegrityError: duplicate edge (same source, target, scenario)
    """
    if source_component_id == target_component_id:
        raise ValueError("Self-loops are not permitted: source and target must be different components.")

    # Cross-scenario validation
    src = conn.execute(
        "SELECT scenario_id FROM components WHERE id = ?", (source_component_id,)
    ).fetchone()
    tgt = conn.execute(
        "SELECT scenario_id FROM components WHERE id = ?", (target_component_id,)
    ).fetchone()

    if src is None:
        raise ValueError(f"source_component_id '{source_component_id}' not found.")
    if tgt is None:
        raise ValueError(f"target_component_id '{target_component_id}' not found.")
    if src["scenario_id"] != scenario_id:
        raise ValueError(
            f"source_component_id '{source_component_id}' does not belong to scenario '{scenario_id}'."
        )
    if tgt["scenario_id"] != scenario_id:
        raise ValueError(
            f"target_component_id '{target_component_id}' does not belong to scenario '{scenario_id}'."
        )

    edge_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO edges (
            id, scenario_id, source_component_id, target_component_id,
            label, evidence_source, confirmation_status, last_observed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            edge_id, scenario_id, source_component_id, target_component_id,
            label, evidence_source, confirmation_status, last_observed_at,
        ),
    )
    conn.commit()
    return get_edge(conn, scenario_id, edge_id)  # type: ignore[return-value]


def get_edge(
    conn: sqlite3.Connection, scenario_id: str, edge_id: str
) -> Optional[dict]:
    """Return a single edge by ID within a scenario, or None."""
    row = conn.execute(
        "SELECT * FROM edges WHERE id = ? AND scenario_id = ?",
        (edge_id, scenario_id),
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_edges(conn: sqlite3.Connection, scenario_id: str) -> list[dict]:
    """Return all edges for a scenario."""
    rows = conn.execute(
        "SELECT * FROM edges WHERE scenario_id = ? ORDER BY id ASC",
        (scenario_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_edge(
    conn: sqlite3.Connection,
    scenario_id: str,
    edge_id: str,
    label: Optional[str] = None,
    evidence_source: Optional[str] = None,
    confirmation_status: Optional[str] = None,
    last_observed_at: Optional[str] = None,
) -> Optional[dict]:
    """
    Update mutable edge fields (label, evidence_source, confirmation_status, last_observed_at).
    source_component_id and target_component_id are IMMUTABLE and cannot be updated.
    Returns None if edge not found.
    """
    fields: dict[str, Any] = {}
    if label is not None:
        fields["label"] = label
    if evidence_source is not None:
        fields["evidence_source"] = evidence_source
    if confirmation_status is not None:
        fields["confirmation_status"] = confirmation_status
    if last_observed_at is not None:
        fields["last_observed_at"] = last_observed_at

    if not fields:
        return get_edge(conn, scenario_id, edge_id)

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [edge_id, scenario_id]
    conn.execute(
        f"UPDATE edges SET {set_clause} WHERE id = ? AND scenario_id = ?",
        values,
    )
    conn.commit()
    return get_edge(conn, scenario_id, edge_id)


def delete_edge(
    conn: sqlite3.Connection, scenario_id: str, edge_id: str
) -> bool:
    """Delete an edge. Returns True if deleted, False if not found."""
    cursor = conn.execute(
        "DELETE FROM edges WHERE id = ? AND scenario_id = ?",
        (edge_id, scenario_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def edge_exists(
    conn: sqlite3.Connection,
    scenario_id: str,
    source_component_id: str,
    target_component_id: str,
) -> bool:
    """Return True if an edge with this source, target, and scenario already exists."""
    row = conn.execute(
        """SELECT 1 FROM edges
           WHERE scenario_id = ? AND source_component_id = ? AND target_component_id = ?""",
        (scenario_id, source_component_id, target_component_id),
    ).fetchone()
    return row is not None
