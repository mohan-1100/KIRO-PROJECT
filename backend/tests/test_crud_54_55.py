"""
Acceptance tests for tasks 5.4 and 5.5:
  - simulation_history CRUD (create + get round-trip)
  - settings CRUD (default, set/get, boundary validation)
"""
import sqlite3
import pytest

from app.db.crud.simulation_history import (
    create_simulation_record,
    get_simulation_record,
    list_simulation_history,
    list_all_incidents,
    update_incident_status,
)
from app.db.crud.settings import (
    get_setting,
    set_setting,
    get_freshness_threshold,
    set_freshness_threshold,
    get_all_settings,
)


@pytest.fixture()
def mem_db():
    """In-memory SQLite DB with the required tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE scenarios (
            id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
            description TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE simulation_history (
            id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            failed_target_id TEXT NOT NULL,
            failed_target_type TEXT NOT NULL,
            failure_type TEXT NOT NULL,
            directly_affected_count INTEGER NOT NULL DEFAULT 0,
            transitively_affected_count INTEGER NOT NULL DEFAULT 0,
            impact_score INTEGER NOT NULL DEFAULT 0
                CHECK(impact_score BETWEEN 0 AND 100),
            data_confidence_score INTEGER NOT NULL DEFAULT 100
                CHECK(data_confidence_score BETWEEN 0 AND 100),
            status TEXT NOT NULL DEFAULT 'open',
            full_report_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT INTO scenarios VALUES ('s1', 'Test Scenario', NULL, '2024-01-01T00:00:00');
    """)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# simulation_history tests
# ---------------------------------------------------------------------------

def test_create_and_get_round_trip(mem_db):
    record = create_simulation_record(
        mem_db,
        record_id="rec-1",
        scenario_id="s1",
        timestamp="2024-06-01T12:00:00",
        failed_target_id="comp-a",
        failed_target_type="component",
        failure_type="component_unavailable",
        directly_affected_count=2,
        transitively_affected_count=3,
        impact_score=75,
        data_confidence_score=80,
        full_report={"summary": "test", "affected": ["b", "c"]},
    )
    assert record["id"] == "rec-1"
    assert record["scenario_id"] == "s1"
    assert record["impact_score"] == 75
    assert record["full_report"] == {"summary": "test", "affected": ["b", "c"]}
    assert "full_report_json" not in record

    fetched = get_simulation_record(mem_db, "rec-1")
    assert fetched is not None
    assert fetched["id"] == "rec-1"
    assert fetched["full_report"]["summary"] == "test"


def test_get_nonexistent_returns_none(mem_db):
    assert get_simulation_record(mem_db, "does-not-exist") is None


def test_list_simulation_history_reverse_chronological(mem_db):
    create_simulation_record(
        mem_db, "r1", "s1", "2024-01-01T10:00:00", "c1", "component",
        "component_unavailable", 1, 0, 10, 90, {},
    )
    create_simulation_record(
        mem_db, "r2", "s1", "2024-01-02T10:00:00", "c2", "component",
        "component_unavailable", 1, 0, 20, 90, {},
    )
    results = list_simulation_history(mem_db, "s1")
    assert [r["id"] for r in results] == ["r2", "r1"]


def test_list_all_incidents(mem_db):
    create_simulation_record(
        mem_db, "r1", "s1", "2024-01-01T10:00:00", "c1", "component",
        "component_unavailable", 1, 0, 10, 90, {},
    )
    incidents = list_all_incidents(mem_db)
    assert len(incidents) == 1
    assert incidents[0]["id"] == "r1"


def test_update_incident_status(mem_db):
    create_simulation_record(
        mem_db, "r1", "s1", "2024-01-01T10:00:00", "c1", "component",
        "component_unavailable", 1, 0, 10, 90, {},
    )
    updated = update_incident_status(mem_db, "r1", "resolved")
    assert updated is not None
    assert updated["status"] == "resolved"


def test_update_incident_status_not_found(mem_db):
    result = update_incident_status(mem_db, "no-such-id", "resolved")
    assert result is None


# ---------------------------------------------------------------------------
# settings tests
# ---------------------------------------------------------------------------

def test_get_freshness_threshold_default_72(mem_db):
    assert get_freshness_threshold(mem_db) == 72


def test_set_freshness_threshold_persists(mem_db):
    set_freshness_threshold(mem_db, 48)
    assert get_freshness_threshold(mem_db) == 48


def test_set_freshness_threshold_zero_raises(mem_db):
    with pytest.raises(ValueError):
        set_freshness_threshold(mem_db, 0)


def test_set_freshness_threshold_too_large_raises(mem_db):
    with pytest.raises(ValueError):
        set_freshness_threshold(mem_db, 8761)


def test_set_freshness_threshold_boundary_values(mem_db):
    set_freshness_threshold(mem_db, 1)
    assert get_freshness_threshold(mem_db) == 1
    set_freshness_threshold(mem_db, 8760)
    assert get_freshness_threshold(mem_db) == 8760


def test_get_setting_missing_returns_none(mem_db):
    assert get_setting(mem_db, "nonexistent_key") is None


def test_set_and_get_setting(mem_db):
    set_setting(mem_db, "my_key", "my_value")
    assert get_setting(mem_db, "my_key") == "my_value"


def test_get_all_settings(mem_db):
    set_setting(mem_db, "key1", "val1")
    set_setting(mem_db, "key2", "val2")
    all_settings = get_all_settings(mem_db)
    assert all_settings["key1"] == "val1"
    assert all_settings["key2"] == "val2"
