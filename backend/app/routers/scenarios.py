"""Scenario CRUD and graph endpoints."""
from fastapi import APIRouter, HTTPException
from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import components as component_crud
from app.db.crud import edges as edge_crud
from app.models.scenario import ScenarioCreate, ScenarioResponse
from app.models.common import ProblemDetail
import sqlite3

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios():
    with get_db() as db:
        return scenario_crud.list_scenarios(db)


@router.post("", response_model=ScenarioResponse, status_code=201)
def create_scenario(body: ScenarioCreate):
    with get_db() as db:
        try:
            return scenario_crud.create_scenario(db, body.name, body.description)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail=f"A scenario named '{body.name}' already exists.")


@router.delete("/{scenario_id}", status_code=200)
def delete_scenario(scenario_id: str):
    with get_db() as db:
        deleted = scenario_crud.delete_scenario(db, scenario_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
        return {"detail": "Scenario deleted."}


@router.get("/{scenario_id}/graph")
def get_graph(scenario_id: str):
    with get_db() as db:
        if not scenario_crud.scenario_exists(db, scenario_id):
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
        components = component_crud.list_components(db, scenario_id)
        edges = edge_crud.list_edges(db, scenario_id)
        return {"scenario_id": scenario_id, "components": components, "edges": edges}
