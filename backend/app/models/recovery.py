"""Pydantic models for Recovery Planner endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class RecoveryRequest(BaseModel):
    recovery_type: str = Field(..., pattern="^(component|edge)$")
    recovery_target_id: str


class RecoveryOption(BaseModel):
    recovery_target_id: str
    recovery_type: str
    services_recovered: list[str] = Field(default_factory=list)
    services_recovered_count: int = 0
    services_still_affected: list[str] = Field(default_factory=list)
    services_still_affected_count: int = 0
    projected_impact_score: int = Field(ge=0, le=100)
    simulated_projection_label: str = "Simulated Projection"
    disclosure: str = (
        "Recovery analysis is a simulated projection. It does not account for "
        "configuration, data consistency, capacity, or routing factors not "
        "represented in the dependency graph."
    )
    no_additional_recovery: bool = False


class RecoveryResponse(BaseModel):
    options: list[RecoveryOption]
    simulated_projection_label: str = "Simulated Projection"
