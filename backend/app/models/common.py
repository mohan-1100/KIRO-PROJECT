"""
Shared Pydantic models, enums, and constants used across the ImpactLens API.

Includes:
- Component type enum
- Criticality enum with numeric weights
- Health status enum
- Evidence source and confirmation status enums
- RFC 7807 ProblemDetail response model
- CRITICALITY_WEIGHTS dict
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ComponentType(str, Enum):
    web_application = "web_application"
    api_service = "api_service"
    database = "database"
    cache = "cache"
    authentication_service = "authentication_service"
    message_queue = "message_queue"
    payment_service = "payment_service"
    external_api = "external_api"
    load_balancer = "load_balancer"


class Criticality(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class HealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    failed = "failed"
    unknown = "unknown"


class EvidenceSource(str, Enum):
    manually_entered = "manually_entered"
    auto_discovered = "auto_discovered"
    inferred = "inferred"
    simulated_demo = "simulated_demo"
    unknown = "unknown"


class ConfirmationStatus(str, Enum):
    confirmed = "confirmed"
    inferred = "inferred"
    unknown = "unknown"


class FailureType(str, Enum):
    component_unavailable = "component_unavailable"
    component_degraded = "component_degraded"
    dependency_link_unavailable = "dependency_link_unavailable"


class TargetType(str, Enum):
    component = "component"
    edge = "edge"


class IncidentStatus(str, Enum):
    open = "open"
    resolved = "resolved"


# ---------------------------------------------------------------------------
# Criticality weights (used in Impact Score formula)
# ---------------------------------------------------------------------------

CRITICALITY_WEIGHTS: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


# ---------------------------------------------------------------------------
# RFC 7807 Problem Detail error response model
# ---------------------------------------------------------------------------

class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Details for HTTP APIs.
    Returned by all 4xx and 5xx error responses.
    """
    type: str = "https://impactlens.local/errors/generic"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

    model_config = {"json_schema_extra": {
        "example": {
            "type": "https://impactlens.local/errors/not-found",
            "title": "Resource Not Found",
            "status": 404,
            "detail": "Component with id 'abc' not found in scenario 'xyz'.",
            "instance": "/scenarios/xyz/components/abc"
        }
    }}
