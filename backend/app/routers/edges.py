"""Edge CRUD endpoints scoped to a scenario."""
import sqlite3
from fastapi import APIRouter, HTTPException
from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import edges as edge_crud
from app.models.edge import EdgeCreate, EdgeUpdate, EdgeResponse

router = APIRouter(prefix="/scenarios/{scenario_id}/edges", tags=["edges"])


def _require_scenario(db, scenario_id: str):
    if not scenario_crud.scenario_exists(db, scenario_id):
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")


@router.post("", response_model=EdgeResponse, status_code=201)
def create_edge(scenario_id: str, body: EdgeCreate):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        try:
            edge = edge_crud.create_edge(
                db, scenario_id, body.source_component_id, body.target_component_id,
                body.label, body.evidence_source.value, body.confirmation_status.value,
                body.last_observed_at,
            )
            return edge
        except ValueError as e:
            if "Self-loop" in str(e) or "does not belong" in str(e) or "not found" in str(e):
                raise HTTPException(status_code=422, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"Edge from '{body.source_component_id}' to '{body.target_component_id}' already exists in this scenario.",
            )


@router.get("", response_model=list[EdgeResponse])
def list_edges(scenario_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        return edge_crud.list_edges(db, scenario_id)


@router.get("/{edge_id}", response_model=EdgeResponse)
def get_edge(scenario_id: str, edge_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        edge = edge_crud.get_edge(db, scenario_id, edge_id)
        if not edge:
            raise HTTPException(status_code=404, detail=f"Edge '{edge_id}' not found.")
        return edge


@router.put("/{edge_id}", response_model=EdgeResponse)
def update_edge(scenario_id: str, edge_id: str, body: EdgeUpdate):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        fields = body.model_dump(exclude_unset=True)
        if "evidence_source" in fields and fields["evidence_source"] is not None:
            fields["evidence_source"] = fields["evidence_source"].value
        if "confirmation_status" in fields and fields["confirmation_status"] is not None:
            fields["confirmation_status"] = fields["confirmation_status"].value
        edge = edge_crud.update_edge(db, scenario_id, edge_id, **fields)
        if not edge:
            raise HTTPException(status_code=404, detail=f"Edge '{edge_id}' not found.")
        return edge


@router.delete("/{edge_id}", status_code=200)
def delete_edge(scenario_id: str, edge_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        deleted = edge_crud.delete_edge(db, scenario_id, edge_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Edge '{edge_id}' not found.")
        return {"detail": "Edge deleted."}
