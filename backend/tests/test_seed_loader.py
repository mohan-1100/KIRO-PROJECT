"""
Tests for app.seed.seed_loader.run_seed_if_needed().

Uses a temporary SQLite file so the real application database is never touched.
We manually set / restore os.environ["DATABASE_URL"] and evict cached modules
so every code path inside seed_loader (and connection.py) uses the isolated DB.

Note: monkeypatch is function-scoped and cannot be used inside module-scoped
fixtures in pytest.  We use os.environ directly instead.
"""

import importlib
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Module-level state: create + seed one temp DB for the whole module
# ---------------------------------------------------------------------------

_DB_FILE: Path = None  # set during setup


def _evict_app_modules():
    """Remove all cached app.* modules so the new DATABASE_URL is picked up."""
    to_remove = [k for k in list(sys.modules.keys()) if k.startswith("app")]
    for mod in to_remove:
        del sys.modules[mod]


def pytest_configure(config):
    """Not used here — setup is done in the module-scoped fixture."""


@pytest.fixture(scope="module", autouse=True)
def _setup_temp_db(tmp_path_factory):
    """
    Create an isolated SQLite DB for this test module, seed it once,
    and restore the original DATABASE_URL afterwards.
    """
    global _DB_FILE
    db_dir = tmp_path_factory.mktemp("seed_test")
    db_file = db_dir / "test_seed.db"
    _DB_FILE = db_file

    original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

    _evict_app_modules()

    from app.db.schema import create_tables
    from app.seed.seed_loader import run_seed_if_needed

    create_tables()
    run_seed_if_needed()

    yield  # run all module-level tests

    # Restore original env
    if original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = original_url

    _evict_app_modules()


@pytest.fixture(scope="module")
def db_conn(_setup_temp_db):
    """Open a read-only sqlite3 connection to the seeded DB."""
    conn = sqlite3.connect(str(_DB_FILE))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()["cnt"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_exactly_four_scenarios(db_conn):
    """Seed must insert exactly 4 scenarios."""
    assert _count(db_conn, "scenarios") == 4


def test_at_least_one_component(db_conn):
    """Seed must insert at least 1 component."""
    assert _count(db_conn, "components") > 0


def test_idempotent_second_seed():
    """Running run_seed_if_needed a second time must not duplicate any data."""
    # The DB is already seeded.  Call again — must be a no-op.
    _evict_app_modules()
    # Re-apply the env (it may have been cleaned up by another fixture)
    os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
    _evict_app_modules()

    from app.seed.seed_loader import run_seed_if_needed
    run_seed_if_needed()  # second call

    conn = sqlite3.connect(str(_DB_FILE))
    conn.row_factory = sqlite3.Row
    try:
        assert conn.execute("SELECT COUNT(*) as c FROM scenarios").fetchone()["c"] == 4
        assert conn.execute("SELECT COUNT(*) as c FROM components").fetchone()["c"] > 0
    finally:
        conn.close()


def test_at_least_five_distinct_component_types(db_conn):
    """
    Seed fixtures cover at least 5 distinct component types.
    Current fixture types: api_service, authentication_service, database,
    payment_service, web_application.
    """
    rows = db_conn.execute("SELECT DISTINCT type FROM components").fetchall()
    types = {r["type"] for r in rows}
    assert len(types) >= 5, f"Expected ≥ 5 distinct types, found {len(types)}: {types}"


def test_all_four_scenario_names_present(db_conn):
    """All four expected scenario names must be present."""
    rows = db_conn.execute("SELECT name FROM scenarios").fetchall()
    names = {r["name"] for r in rows}
    expected = {
        "Database Failure",
        "Shared Dependency Failure",
        "Alternative Path Available",
        "Incomplete Evidence",
    }
    assert expected.issubset(names), f"Missing scenarios: {expected - names}"


def test_reporting_service_with_low_dq_score(db_conn):
    """
    At least one component (ReportingService in Scenario D) must have
    data_quality_score = 20.
    """
    rows = db_conn.execute(
        "SELECT * FROM components WHERE data_quality_score = 20"
    ).fetchall()
    assert len(rows) >= 1, "Expected at least one component with data_quality_score=20"
    names = [r["name"] for r in rows]
    assert "ReportingService" in names


def test_at_least_one_stale_component(db_conn):
    """
    At least one component's last_observed_at is > 72 hours in the past.
    The fixture for Scenario D has last_observed_at='2023-01-01T00:00:00+00:00'.
    """
    rows = db_conn.execute(
        "SELECT * FROM components WHERE last_observed_at IS NOT NULL"
    ).fetchall()
    threshold = datetime.now(timezone.utc) - timedelta(hours=72)
    stale_found = False
    for row in rows:
        try:
            obs = row["last_observed_at"].replace("Z", "+00:00")
            obs_dt = datetime.fromisoformat(obs)
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
            if obs_dt < threshold:
                stale_found = True
                break
        except (ValueError, AttributeError):
            pass
    assert stale_found, "Expected at least one component with last_observed_at > 72h ago"


def test_seed_inserts_edges(db_conn):
    """Seed must insert at least one edge."""
    assert _count(db_conn, "edges") > 0
