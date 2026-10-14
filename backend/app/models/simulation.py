"""
Pydantic models for Simulation endpoints.

Key design decisions:
- SimulationRequest validates target_type + failure_type combinations
- ImpactReport includes both impact_score and data_confidence_score as separate fields
- possible_alt_path_components reports detected alternative paths without excluding components
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from app.models.common import FailureType, TargetType, IncidentStatus


class SimulationRequest(BaseModel):
    scenario_id: str
    target_type: TargetType
    target_id: str
    failure_type: FailureType

    @model_validator(mode="after")
    def validate_type_combination(self) -> "SimulationRequest":
        """
        Enforce valid target_type + failure_type combinations:
        - component -> component_unavailable or component_degraded
        - edge      -> dependency_link_unavailable
        """
        if self.target_type == TargetType.component:
            if self.failure_type == FailureType.dependency_link_unavailable:
                raise ValueError(
                    "failure_type 'dependency_link_unavailable' is only valid when target_type is 'edge'."
                )
        elif self.target_type == TargetType.edge:
            if self.failure_type in (FailureType.component_unavailable, FailureType.component_degraded):
                raise ValueError(
                    f"failure_type '{self.failure_type}' is only valid when target_type is 'component'."
                )
        return self


class ScoreBreakdown(BaseModel):
    label: str = "ImpactLens heuristic v1.0 — not an industry standard metric"
    criticality_score: dict[str, float]
    reach_score: dict[str, float]
    proximity_score: dict[str, float]
    isolation_score: dict[str, float]


class AffectedComponentSummary(BaseModel):
    component_id: str
    name: str
    criticality: str
    severity_contribution: float
    has_alternative_path: bool
    possible_alternative_sources: list[str] = Field(default_factory=list)


class PathStep(BaseModel):
    component_id: str
    component_name: str
    edge_direction: Optional[str] = "→"


class ImpactPath(BaseModel):
    affected_component_id: str
    affected_component_name: str
    path_steps: list[PathStep]
    explanation_text: str
    has_dq_warning: bool = False
    alternative_paths: list[list[PathStep]] = Field(default_factory=list)


class PossibleAltPathComponent(BaseModel):
    component_id: str
    component_name: str
    possible_alternative_source_names: list[str]
    disclosure: str = (
        "Alternative inbound path detected. Operational equivalence is not verified "
        "— engineer review required before treating this service as unaffected."
    )


class StalenessWarning(BaseModel):
    component_id: str
    component_name: str
    hours_since_observed: float


class ImpactReport(BaseModel):
    sim_id: str
    scenario_id: str
    failed_target_id: str
    failed_target_type: str
    failure_type: str
    impact_score: int = Field(ge=0, le=100)
    data_confidence_score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    low_confidence_notice: Optional[str] = None
    already_failed_warning: bool = False
    directly_affected: list[AffectedComponentSummary] = Field(default_factory=list)
    transitively_affected: list[AffectedComponentSummary] = Field(default_factory=list)
    impact_paths: list[ImpactPath] = Field(default_factory=list)
    possible_alt_path_components: list[PossibleAltPathComponent] = Field(default_factory=list)
    staleness_warnings: list[StalenessWarning] = Field(default_factory=list)
    simulated_projection_label: Optional[str] = None
    timestamp: str


class SimulationHistoryRecord(BaseModel):
    id: str
    scenario_id: str
    timestamp: str
    failed_target_id: str
    failed_target_type: str
    failure_type: str
    directly_affected_count: int
    transitively_affected_count: int
    impact_score: int
    data_confidence_score: int
    status: str
