"""Pydantic models for Edge endpoints."""
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import EvidenceSource, ConfirmationStatus


class EdgeCreate(BaseModel):
    source_component_id: str = Field(..., min_length=1)
    target_component_id: str = Field(..., min_length=1)
    label: Optional[str] = Field(None, max_length=200)
    evidence_source: EvidenceSource = EvidenceSource.unknown
    confirmation_status: ConfirmationStatus = ConfirmationStatus.unknown
    last_observed_at: Optional[str] = None


class EdgeUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=200)
    evidence_source: Optional[EvidenceSource] = None
    confirmation_status: Optional[ConfirmationStatus] = None
    last_observed_at: Optional[str] = None


class EdgeResponse(BaseModel):
    id: str
    scenario_id: str
    source_component_id: str
    target_component_id: str
    label: Optional[str] = None
    evidence_source: str
    confirmation_status: str
    last_observed_at: Optional[str] = None

    model_config = {"from_attributes": True}
