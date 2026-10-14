"""
Data Quality endpoint for ImpactLens.

Returns per-component and per-edge evidence metadata, staleness flags,
and the global Data Completeness Indicator for a scenario.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import components as component_crud
from app.db.crud import edges as edge_crud
from app.db.crud.settings import get_freshness_threshold

router = APIRouter(prefix="/scenarios/{scenario_id}/data-quality", tags=["data-quality"])


@router.get("")
def get_data_quality(scenario_id: str):
    """
    Return evidence metadata, staleness flags, and global Data Completeness Indicator
    for all components and edges in the given scenario.
    """
    with get_db() as db:
        if not scenario_crud.scenario_exists(db, scenario_id):
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

        components = component_crud.list_components(db, scenario_id)
        edges = edge_crud.list_edges(db, scenario_id)
        freshness_hours = get_freshness_threshold(db)

    now = datetime.now(timezone.utc)

    def compute_staleness(last_observed_at: str | None) -> tuple[bool, float | None]:
        if not last_observed_at:
            return False, None
        try:
            obs_dt = datetime.fromisoformat(last_observed_at.replace("Z", "+00:00"))
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
            elapsed = (now - obs_dt).total_seconds() / 3600.0
            return elapsed > freshness_hours, round(elapsed, 1)
        except (ValueError, TypeError):
            return False, None

    # Per-component metadata
    comp_results = []
    confirmed_count = 0
    for comp in components:
        is_stale, hours_elapsed = compute_staleness(comp.get("last_observed_at"))
        if comp.get("confirmation_status") == "confirmed":
            confirmed_count += 1
        comp_results.append({
            "component_id": comp["id"],
            "name": comp["name"],
            "type": comp.get("type"),
            "criticality": comp.get("criticality"),
            "evidence_source": comp.get("evidence_source"),
            "confirmation_status": comp.get("confirmation_status"),
            "data_quality_score": comp.get("data_quality_score"),
            "last_observed_at": comp.get("last_observed_at"),
            "is_stale": is_stale,
            "hours_since_observed": hours_elapsed,
        })

    # Data Completeness Indicator
    total = len(components)
    data_completeness_indicator = (
        round((confirmed_count / total) * 100) if total > 0 else 0
    )

    # Per-edge metadata
    edge_results = []
    for edge in edges:
        is_stale, hours_elapsed = compute_staleness(edge.get("last_observed_at"))
        edge_results.append({
            "edge_id": edge["id"],
            "source_component_id": edge.get("source_component_id"),
            "target_component_id": edge.get("target_component_id"),
            "label": edge.get("label"),
            "evidence_source": edge.get("evidence_source"),
            "confirmation_status": edge.get("confirmation_status"),
            "last_observed_at": edge.get("last_observed_at"),
            "is_stale": is_stale,
            "hours_since_observed": hours_elapsed,
        })

    return {
        "scenario_id": scenario_id,
        "data_completeness_indicator": data_completeness_indicator,
        "freshness_threshold_hours": freshness_hours,
        "components": comp_results,
        "edges": edge_results,
    }
