"""Component CRUD endpoints scoped to a scenario."""
from fastapi import APIRouter, HTTPException
from app.db.connection import get_db
from app.db.crud import scenarios as scenario_crud
from app.db.crud import components as component_crud
from app.models.component import ComponentCreate, ComponentUpdate, ComponentResponse

router = APIRouter(prefix="/scenarios/{scenario_id}/components", tags=["components"])


def _require_scenario(db, scenario_id: str):
    if not scenario_crud.scenario_exists(db, scenario_id):
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")


@router.post("", response_model=ComponentResponse, status_code=201)
def create_component(scenario_id: str, body: ComponentCreate):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        try:
            comp = component_crud.create_component(
                db, scenario_id, body.name, body.type.value, body.criticality.value,
                body.health_status.value, body.last_observed_at, body.evidence_source.value,
                body.confirmation_status.value, body.data_quality_score,
            )
            return comp
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=list[ComponentResponse])
def list_components(scenario_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        return component_crud.list_components(db, scenario_id)


@router.get("/{component_id}", response_model=ComponentResponse)
def get_component(scenario_id: str, component_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        comp = component_crud.get_component(db, scenario_id, component_id)
        if not comp:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")
        return comp


@router.put("/{component_id}", response_model=ComponentResponse)
def update_component(scenario_id: str, component_id: str, body: ComponentUpdate):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        fields = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
        # Convert enums to their string values
        for key in ("type", "criticality", "health_status", "evidence_source", "confirmation_status"):
            if key in fields and hasattr(fields[key], "value"):
                fields[key] = fields[key].value
        try:
            comp = component_crud.update_component(db, scenario_id, component_id, **fields)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        if not comp:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")
        return comp


@router.delete("/{component_id}", status_code=200)
def delete_component(scenario_id: str, component_id: str):
    with get_db() as db:
        _require_scenario(db, scenario_id)
        success, edge_ids = component_crud.delete_component(db, scenario_id, component_id)
        if edge_ids:
            raise HTTPException(
                status_code=409,
                detail={"message": "Cannot delete component with existing edges.", "edge_ids": edge_ids},
            )
        if not success:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")
        return {"detail": "Component deleted."}
