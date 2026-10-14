"""Pydantic models for Scenario endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}
