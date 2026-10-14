"""Simulation endpoints — run, retrieve, reset, and recover."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response

from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import components as component_crud
from app.db.crud import edges as edge_crud
from app.db.crud import simulation_history as history_crud
from app.db.crud.settings import get_freshness_threshold
from app.engine.active_simulation_store import ActiveSimulation, active_sim_store
from app.engine.graph_builder import build_simulation_graph
from app.engine.impact_engine import build_impact_report
from app.engine.recovery_engine import compute_recovery_options
from app.models.simulation import SimulationRequest, ImpactReport, SimulationHistoryRecord
from app.models.recovery import RecoveryRequest, RecoveryResponse

router = APIRouter(prefix="/scenarios/{scenario_id}", tags=["simulations"])


def _require_scenario(db, scenario_id: str):
    if not scenario_crud.scenario_exists(db, scenario_id):
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found.")


@router.post("/simulations", response_model=ImpactReport)
def run_simulation(scenario_id: str, body: SimulationRequest):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        if body.target_type.value == "component":
            if not component_crud.get_component(db, scenario_id, body.target_id):
                raise HTTPException(404, detail=f"Component '{body.target_id}' not found in scenario.")
        else:
            if not edge_crud.get_edge(db, scenario_id, body.target_id):
                raise HTTPException(404, detail=f"Edge '{body.target_id}' not found in scenario.")
        components = component_crud.list_components(db, scenario_id)
        edges = edge_crud.list_edges(db, scenario_id)
        freshness = get_freshness_threshold(db)

    sim_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    temp_sim = ActiveSimulation(
        scenario_id=scenario_id, sim_id=sim_id,
        target_type=body.target_type.value, target_id=body.target_id,
        failure_type=body.failure_type.value, impact_report={},
    )

    report = build_impact_report(components, edges, temp_sim, freshness)

    with get_db() as db:
        history_crud.create_simulation_record(
            db, record_id=sim_id, scenario_id=scenario_id, timestamp=now,
            failed_target_id=body.target_id, failed_target_type=body.target_type.value,
            failure_type=body.failure_type.value,
            directly_affected_count=len(report.directly_affected),
            transitively_affected_count=len(report.transitively_affected),
            impact_score=report.impact_score,
            data_confidence_score=report.data_confidence_score,
            full_report=report.model_dump(), status="open",
        )

    temp_sim.impact_report = report.model_dump()
    active_sim_store.set(scenario_id, temp_sim)
    return report


@router.get("/simulations", response_model=list[SimulationHistoryRecord])
def list_simulations(scenario_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        return history_crud.list_simulation_history(db, scenario_id)


@router.get("/simulation")
def get_active_simulation(scenario_id: str, response: Response):
    with get_db() as db:
        _require_scenario(db, scenario_id)
    sim = active_sim_store.get(scenario_id)
    if sim is None:
        response.status_code = 204
        return None
    return sim.impact_report


@router.post("/reset")
def reset_simulation(scenario_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        records = history_crud.list_simulation_history(db, scenario_id)
        for r in records:
            if r.get("status") == "open":
                history_crud.update_incident_status(db, r["id"], "resolved")
    active_sim_store.clear(scenario_id)
    return {"detail": "Simulation reset."}


@router.post("/simulations/{sim_id}/recovery", response_model=RecoveryResponse)
def get_recovery_options(scenario_id: str, sim_id: str, body: RecoveryRequest):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        components = component_crud.list_components(db, scenario_id)
        edges = edge_crud.list_edges(db, scenario_id)

    active_sim = active_sim_store.get(scenario_id)
    if active_sim is None:
        raise HTTPException(400, detail="No active simulation for this scenario.")
    if active_sim.sim_id != sim_id:
        raise HTTPException(404, detail=f"Simulation '{sim_id}' not found.")

    if body.recovery_type == "component":
        G, _, _ = build_simulation_graph(components, edges, active_sim)
        if body.recovery_target_id not in G:
            raise HTTPException(404, detail=f"Component '{body.recovery_target_id}' not found.")
        health = G.nodes[body.recovery_target_id].get("health_status", "unknown")
        if health not in ("failed", "degraded"):
            raise HTTPException(400, detail=f"Component '{body.recovery_target_id}' is not a valid recovery candidate.")

    G, _, _ = build_simulation_graph(components, edges, active_sim)
    report = active_sim.impact_report
    original_directly = {c["component_id"]: 1 for c in report.get("directly_affected", [])}
    original_transitively = {c["component_id"]: 2 for c in report.get("transitively_affected", [])}
    original_impacted = {**original_directly, **original_transitively}

    options = compute_recovery_options(G, active_sim, original_impacted, components)
    return RecoveryResponse(options=options)
