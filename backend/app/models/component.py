"""Pydantic models for Component endpoints."""
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import ComponentType, Criticality, HealthStatus, EvidenceSource, ConfirmationStatus


class ComponentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: ComponentType
    criticality: Criticality
    health_status: HealthStatus = HealthStatus.unknown
    last_observed_at: Optional[str] = None
    evidence_source: EvidenceSource = EvidenceSource.unknown
    confirmation_status: ConfirmationStatus = ConfirmationStatus.unknown
    data_quality_score: int = Field(default=50, ge=0, le=100)


class ComponentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[ComponentType] = None
    criticality: Optional[Criticality] = None
    health_status: Optional[HealthStatus] = None
    last_observed_at: Optional[str] = None
    evidence_source: Optional[EvidenceSource] = None
    confirmation_status: Optional[ConfirmationStatus] = None
    data_quality_score: Optional[int] = Field(None, ge=0, le=100)


class ComponentResponse(BaseModel):
    id: str
    scenario_id: str
    name: str
    type: str
    criticality: str
    health_status: str
    last_observed_at: Optional[str] = None
    evidence_source: str
    confirmation_status: str
    data_quality_score: int

    model_config = {"from_attributes": True}
