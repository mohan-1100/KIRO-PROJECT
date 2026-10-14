"""
Database schema creation for ImpactLens.

Defines all SQLite tables, indexes, and constraints. Called once at
API startup via the FastAPI lifespan hook. Uses CREATE TABLE IF NOT EXISTS
so it is safe to call on every startup.

Tables:
  - scenarios          : named infrastructure configurations
  - components         : infrastructure nodes (scoped to a scenario)
  - edges              : directed dependency relationships (scoped to a scenario)
  - simulation_history : persisted record of every completed simulation
  - settings           : key-value application configuration

Graph semantics: edge A -> B means B depends on A. If A fails, B may be affected.
"""

import sqlite3

from app.db.connection import get_db_connection


def create_tables() -> None:
    """
    Create all ImpactLens database tables and indexes if they do not exist.
    Insert the default settings row (freshness_threshold_hours = 72).
    Safe to call on every server startup.
    """
    conn = get_db_connection()
    try:
        _create_scenarios(conn)
        _create_components(conn)
        _create_edges(conn)
        _create_simulation_history(conn)
        _create_settings(conn)
        _create_indexes(conn)
        _insert_default_settings(conn)
        conn.commit()
    finally:
        conn.close()


def _create_scenarios(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at  TEXT NOT NULL
        )
    """)


def _create_components(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id                  TEXT PRIMARY KEY,
            scenario_id         TEXT NOT NULL
                                    REFERENCES scenarios(id) ON DELETE CASCADE,
            name                TEXT NOT NULL,
            type                TEXT NOT NULL,
            criticality         TEXT NOT NULL DEFAULT 'low',
            health_status       TEXT NOT NULL DEFAULT 'unknown',
            last_observed_at    TEXT,
            evidence_source     TEXT NOT NULL DEFAULT 'unknown',
            confirmation_status TEXT NOT NULL DEFAULT 'unknown',
            data_quality_score  INTEGER NOT NULL DEFAULT 50
                                    CHECK(data_quality_score BETWEEN 0 AND 100)
        )
    """)


def _create_edges(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id                    TEXT PRIMARY KEY,
            scenario_id           TEXT NOT NULL
                                      REFERENCES scenarios(id) ON DELETE CASCADE,
            source_component_id   TEXT NOT NULL
                                      REFERENCES components(id),
            target_component_id   TEXT NOT NULL
                                      REFERENCES components(id),
            label                 TEXT,
            evidence_source       TEXT NOT NULL DEFAULT 'unknown',
            confirmation_status   TEXT NOT NULL DEFAULT 'unknown',
            last_observed_at      TEXT,
            UNIQUE(scenario_id, source_component_id, target_component_id)
        )
    """)


def _create_simulation_history(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulation_history (
            id                          TEXT PRIMARY KEY,
            scenario_id                 TEXT NOT NULL
                                            REFERENCES scenarios(id) ON DELETE CASCADE,
            timestamp                   TEXT NOT NULL,
            failed_target_id            TEXT NOT NULL,
            failed_target_type          TEXT NOT NULL,
            failure_type                TEXT NOT NULL,
            directly_affected_count     INTEGER NOT NULL DEFAULT 0,
            transitively_affected_count INTEGER NOT NULL DEFAULT 0,
            impact_score                INTEGER NOT NULL DEFAULT 0
                                            CHECK(impact_score BETWEEN 0 AND 100),
            data_confidence_score       INTEGER NOT NULL DEFAULT 100
                                            CHECK(data_confidence_score BETWEEN 0 AND 100),
            status                      TEXT NOT NULL DEFAULT 'open',
            full_report_json            TEXT NOT NULL DEFAULT '{}'
        )
    """)


def _create_settings(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)


def _create_indexes(conn: sqlite3.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_components_scenario ON components(scenario_id)",
        "CREATE INDEX IF NOT EXISTS idx_edges_scenario   ON edges(scenario_id)",
        "CREATE INDEX IF NOT EXISTS idx_edges_source     ON edges(source_component_id)",
        "CREATE INDEX IF NOT EXISTS idx_edges_target     ON edges(target_component_id)",
        "CREATE INDEX IF NOT EXISTS idx_simhist_scenario ON simulation_history(scenario_id)",
        "CREATE INDEX IF NOT EXISTS idx_simhist_status   ON simulation_history(status)",
    ]
    for sql in indexes:
        conn.execute(sql)


def _insert_default_settings(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
        ("freshness_threshold_hours", "72"),
    )


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all ImpactLens tables. Used in tests for clean state.
    Order matters due to foreign key constraints.
    """
    tables = [
        "simulation_history",
        "edges",
        "components",
        "scenarios",
        "settings",
    ]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
