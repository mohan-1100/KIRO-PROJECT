"""Incident endpoints — simulation history records with status tracking."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.connection import get_db
from app.db.crud import simulation_history as history_crud

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentStatusUpdate(BaseModel):
    status: str


@router.get("")
def list_incidents():
    """Return all incidents across all scenarios in reverse-chronological order."""
    with get_db() as db:
        incidents = history_crud.list_all_incidents(db)
        return incidents


@router.patch("/{incident_id}")
def update_incident_status(incident_id: str, body: IncidentStatusUpdate):
    """Mark an incident as resolved. Only 'resolved' is accepted."""
    if body.status != "resolved":
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{body.status}'. Only 'resolved' is accepted.",
        )
    with get_db() as db:
        updated = history_crud.update_incident_status(db, incident_id, body.status)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
        return updated
