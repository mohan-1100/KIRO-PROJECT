"""Settings endpoints — application configuration (freshness threshold, etc.)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.db.connection import get_db
from app.db.crud.settings import get_freshness_threshold, set_freshness_threshold

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    freshness_threshold_hours: int = Field(..., ge=1, le=8760)


@router.get("")
def get_settings():
    with get_db() as db:
        return {"freshness_threshold_hours": get_freshness_threshold(db)}


@router.put("")
def update_settings(body: SettingsUpdate):
    with get_db() as db:
        set_freshness_threshold(db, body.freshness_threshold_hours)
        return {"freshness_threshold_hours": get_freshness_threshold(db)}
