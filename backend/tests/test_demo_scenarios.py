"""
Integration tests for the four ImpactLens demo scenarios using FastAPI TestClient.

Scenario A  "Database Failure"
  - Fail OrderDB (component_unavailable) in scenario sc-a
  - OrderService and ReportingService must appear in affected

Scenario B  "Shared Dependency Failure"
  - Fail AuthService (component_unavailable) in scenario sc-b
  - OrderService, PaymentService, UserService all appear in affected

Scenario C  "Alternative Path Available"
  - Fail UserDB (component_unavailable) in scenario sc-c
  - InventoryService appears in possible_alt_path_components

Scenario D  "Incomplete Evidence"
  - Fail OrderDB (component_unavailable) in scenario sc-d
  - data_confidence_score is reduced (< 100) because ReportingService has DQ=20
  - ReportingService path has has_dq_warning=True

Determinism
  - Same simulation twice → identical impact_score and identical affected set

Note: monkeypatch is function-scoped; we manage DATABASE_URL via os.environ directly
inside a module-scoped fixture to avoid pytest ScopeMismatch errors.
"""

import os
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# IDs from fixtures
# ---------------------------------------------------------------------------

SC_A = "sc-a0000000-0000-0000-0000-000000000001"
SC_B = "sc-b0000000-0000-0000-0000-000000000002"
SC_C = "sc-c0000000-0000-0000-0000-000000000003"
SC_D = "sc-d0000000-0000-0000-0000-000000000004"

ORDERDB_A = "c-orderdb-00000000-0000-0000-0000-000000000001"
AUTHSVC_B  = "c-authsvc-00000000-0000-0000-0000-000000000005"
USERDB_C   = "c-userdb-c-00000000-0000-0000-0000-000000000010"
ORDERDB_D  = "c-orderdb-d-00000000-0000-0000-0000-000000000013"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _evict_app_modules():
    to_remove = [k for k in list(sys.modules.keys()) if k.startswith("app")]
    for mod in to_remove:
        del sys.modules[mod]


# ---------------------------------------------------------------------------
# Module-scoped fixture: isolated DB + TestClient created once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """
    Spin up a FastAPI TestClient pointed at an isolated temp DB.
    Seeds the DB via the lifespan startup hook.
    DATABASE_URL is set manually (not via monkeypatch) so it works at module scope.
    """
    db_file = tmp_path_factory.mktemp("demo_scenarios") / "demo.db"
    db_url = f"sqlite:///{db_file}"

    original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url

    # Ensure a clean import of the whole app
    _evict_app_modules()

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as tc:
        yield tc

    # Restore
    if original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = original_url

    _evict_app_modules()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _run_simulation(client, scenario_id, target_id, failure_type="component_unavailable", target_type="component"):
    payload = {
        "scenario_id": scenario_id,
        "target_type": target_type,
        "target_id": target_id,
        "failure_type": failure_type,
    }
    resp = client.post(f"/scenarios/{scenario_id}/simulations", json=payload)
    assert resp.status_code == 200, f"Simulation failed: {resp.status_code} {resp.text}"
    return resp.json()


def _all_affected_names(report):
    """Collect names from directly_affected + transitively_affected."""
    names = set()
    for comp in report.get("directly_affected", []):
        names.add(comp["name"])
    for comp in report.get("transitively_affected", []):
        names.add(comp["name"])
    return names


def _reset(client, scenario_id):
    client.post(f"/scenarios/{scenario_id}/reset")


# ---------------------------------------------------------------------------
# Scenario A: Database Failure
# ---------------------------------------------------------------------------

def test_scenario_a_orderservice_affected(client):
    """Failing OrderDB → OrderService must be in affected."""
    _reset(client, SC_A)
    report = _run_simulation(client, SC_A, ORDERDB_A)
    names = _all_affected_names(report)
    assert "OrderService" in names, f"Expected OrderService in affected, got: {names}"


def test_scenario_a_reporting_service_affected(client):
    """Failing OrderDB → ReportingService must be in affected."""
    _reset(client, SC_A)
    report = _run_simulation(client, SC_A, ORDERDB_A)
    names = _all_affected_names(report)
    assert "ReportingService" in names, f"Expected ReportingService in affected, got: {names}"


def test_scenario_a_impact_score_positive(client):
    """Failing a critical DB must produce a positive impact score."""
    _reset(client, SC_A)
    report = _run_simulation(client, SC_A, ORDERDB_A)
    assert report["impact_score"] > 0


# ---------------------------------------------------------------------------
# Scenario B: Shared Dependency Failure
# ---------------------------------------------------------------------------

def test_scenario_b_all_dependants_affected(client):
    """Failing AuthService → OrderService, PaymentService, UserService all in affected."""
    _reset(client, SC_B)
    report = _run_simulation(client, SC_B, AUTHSVC_B)
    names = _all_affected_names(report)
    for expected in ("OrderService", "PaymentService", "UserService"):
        assert expected in names, f"Expected {expected} in affected, got: {names}"


def test_scenario_b_shopping_app_transitively_affected(client):
    """ShoppingApp (2 hops from AuthService) must be in affected."""
    _reset(client, SC_B)
    report = _run_simulation(client, SC_B, AUTHSVC_B)
    names = _all_affected_names(report)
    assert "ShoppingApp" in names, f"Expected ShoppingApp transitively affected, got: {names}"


def test_scenario_b_high_impact_score(client):
    """Failing a shared critical service (fan-out) should produce a meaningful impact score."""
    _reset(client, SC_B)
    report = _run_simulation(client, SC_B, AUTHSVC_B)
    assert report["impact_score"] >= 20, f"Expected meaningful score, got: {report['impact_score']}"


# ---------------------------------------------------------------------------
# Scenario C: Alternative Path Available
# ---------------------------------------------------------------------------

def test_scenario_c_inventoryservice_in_possible_alts(client):
    """Failing UserDB → InventoryService appears in possible_alt_path_components."""
    _reset(client, SC_C)
    report = _run_simulation(client, SC_C, USERDB_C)
    alt_names = [p["component_name"] for p in report.get("possible_alt_path_components", [])]
    assert "InventoryService" in alt_names, (
        f"Expected InventoryService in possible_alt_path_components, got: {alt_names}"
    )


def test_scenario_c_inventoryservice_still_in_affected(client):
    """
    InventoryService should also appear in affected (conservative behaviour)
    even though an alternative path exists.
    """
    _reset(client, SC_C)
    report = _run_simulation(client, SC_C, USERDB_C)
    names = _all_affected_names(report)
    assert "InventoryService" in names, (
        f"InventoryService should remain in affected conservatively, got: {names}"
    )


def test_scenario_c_alt_component_has_alternative_source(client):
    """The possible_alt_path_components entry for InventoryService lists at least one alt source."""
    _reset(client, SC_C)
    report = _run_simulation(client, SC_C, USERDB_C)
    alts = {p["component_name"]: p for p in report.get("possible_alt_path_components", [])}
    assert "InventoryService" in alts
    inv_entry = alts["InventoryService"]
    alt_sources = inv_entry.get("possible_alternative_source_names", [])
    assert len(alt_sources) >= 1, f"Expected at least one alt source, got: {alt_sources}"


# ---------------------------------------------------------------------------
# Scenario D: Incomplete Evidence
# ---------------------------------------------------------------------------

def test_scenario_d_reduced_data_confidence(client):
    """
    Failing OrderDB in scenario D → data_confidence_score < 100
    because ReportingService has data_quality_score=20.
    """
    _reset(client, SC_D)
    report = _run_simulation(client, SC_D, ORDERDB_D)
    dcs = report["data_confidence_score"]
    assert dcs < 100, f"Expected data_confidence_score < 100 (low DQ fixture), got: {dcs}"


def test_scenario_d_reporting_path_has_dq_warning(client):
    """The impact path for ReportingService must have has_dq_warning=True."""
    _reset(client, SC_D)
    report = _run_simulation(client, SC_D, ORDERDB_D)
    paths = report.get("impact_paths", [])
    reporting_paths = [p for p in paths if p["affected_component_name"] == "ReportingService"]
    assert reporting_paths, "No impact path found for ReportingService"
    assert reporting_paths[0]["has_dq_warning"], (
        "Expected has_dq_warning=True for ReportingService path"
    )


def test_scenario_d_staleness_warning_present(client):
    """
    Scenario D fixture: ReportingService last_observed_at='2023-01-01' which is well
    beyond the 72 h threshold.  staleness_warnings must be non-empty.
    Note: staleness is checked against affected[], and ReportingService is in affected.
    """
    _reset(client, SC_D)
    report = _run_simulation(client, SC_D, ORDERDB_D)
    staleness = report.get("staleness_warnings", [])
    assert len(staleness) >= 1, (
        f"Expected staleness_warnings for stale ReportingService, got: {staleness}"
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_determinism_same_impact_score(client):
    """Running the same simulation twice must produce the identical impact_score."""
    _reset(client, SC_A)
    r1 = _run_simulation(client, SC_A, ORDERDB_A)
    _reset(client, SC_A)
    r2 = _run_simulation(client, SC_A, ORDERDB_A)
    assert r1["impact_score"] == r2["impact_score"], (
        f"Non-deterministic impact scores: {r1['impact_score']} vs {r2['impact_score']}"
    )


def test_determinism_same_affected_set(client):
    """Running the same simulation twice must produce the identical affected component names."""
    _reset(client, SC_A)
    r1 = _run_simulation(client, SC_A, ORDERDB_A)
    _reset(client, SC_A)
    r2 = _run_simulation(client, SC_A, ORDERDB_A)
    assert _all_affected_names(r1) == _all_affected_names(r2), (
        f"Non-deterministic affected sets: {_all_affected_names(r1)} vs {_all_affected_names(r2)}"
    )


def test_determinism_same_dcs(client):
    """Same simulation twice → identical data_confidence_score."""
    _reset(client, SC_A)
    r1 = _run_simulation(client, SC_A, ORDERDB_A)
    _reset(client, SC_A)
    r2 = _run_simulation(client, SC_A, ORDERDB_A)
    assert r1["data_confidence_score"] == r2["data_confidence_score"]
