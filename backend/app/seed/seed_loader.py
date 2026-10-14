"""
Seed Loader for ImpactLens.

Inserts demo data into an empty database on first startup.
Idempotent: does nothing if components already exist.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import components as component_crud
from app.db.crud import edges as edge_crud


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_seed_if_needed() -> None:
    """Insert demo data only if the DB has no components yet."""
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM components").fetchone()
        if row and row["cnt"] > 0:
            return  # Already seeded

    _seed_all()


def _seed_all() -> None:
    """Load fixtures and insert all seed data."""
    scenarios_file = FIXTURES_DIR / "scenarios.json"
    components_file = FIXTURES_DIR / "components.json"
    edges_file = FIXTURES_DIR / "edges.json"

    if not scenarios_file.exists():
        return  # Fixtures not yet created

    with open(scenarios_file) as f:
        scenarios_data = json.load(f)
    with open(components_file) as f:
        components_data = json.load(f)
    with open(edges_file) as f:
        edges_data = json.load(f)

    with get_db() as db:
        # Insert scenarios
        for s in scenarios_data:
            try:
                db.execute(
                    "INSERT OR IGNORE INTO scenarios (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                    (s["id"], s["name"], s.get("description"), s["created_at"]),
                )
            except Exception:
                pass

        # Insert components
        for c in components_data:
            try:
                db.execute(
                    """INSERT OR IGNORE INTO components
                       (id, scenario_id, name, type, criticality, health_status,
                        last_observed_at, evidence_source, confirmation_status, data_quality_score)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        c["id"], c["scenario_id"], c["name"], c["type"],
                        c.get("criticality", "low"), c.get("health_status", "healthy"),
                        c.get("last_observed_at"), c.get("evidence_source", "simulated_demo"),
                        c.get("confirmation_status", "inferred"), c.get("data_quality_score", 75),
                    ),
                )
            except Exception:
                pass

        # Insert edges
        for e in edges_data:
            try:
                db.execute(
                    """INSERT OR IGNORE INTO edges
                       (id, scenario_id, source_component_id, target_component_id,
                        label, evidence_source, confirmation_status, last_observed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        e["id"], e["scenario_id"], e["source_component_id"],
                        e["target_component_id"], e.get("label"),
                        e.get("evidence_source", "simulated_demo"),
                        e.get("confirmation_status", "inferred"),
                        e.get("last_observed_at"),
                    ),
                )
            except Exception:
                pass
        db.commit()
