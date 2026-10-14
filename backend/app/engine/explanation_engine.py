"""
ImpactLens Explanation Engine.

Generates human-readable impact explanations using a template registry.
No LLM or external AI — pure deterministic string formatting.

Templates are keyed by (impact_type, has_alternative, has_dq_warning)
where:
  impact_type    : "direct" (1 hop) | "indirect" (2+ hops)
  has_alternative: True if any alternative sources were detected
  has_dq_warning : True if any component in the path has DQ score < 50
"""

from typing import Any

# ---------------------------------------------------------------------------
# Failure type descriptions
# ---------------------------------------------------------------------------

FAILURE_DESCRIPTIONS: dict[str, str] = {
    "component_unavailable": "unavailable",
    "component_degraded": "degraded",
    "dependency_link_unavailable": "disconnected (link unavailable)",
}

# ---------------------------------------------------------------------------
# Template registry
# keyed by (impact_type, has_alternative, has_dq_warning)
# ---------------------------------------------------------------------------

TEMPLATES: dict[tuple[str, bool, bool], str] = {
    ("direct", False, False): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted."
    ),
    ("direct", True, False): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "Alternative inbound path detected from {alt_path}. "
        "Operational equivalence has not been verified — engineer review recommended."
    ),
    ("direct", False, True): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "{dq_warning}"
    ),
    ("direct", True, True): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "Alternative inbound path detected from {alt_path}. "
        "Operational equivalence has not been verified — engineer review recommended. "
        "{dq_warning}"
    ),
    ("indirect", False, False): (
        "{service} depends on {intermediate_chain}, which depends on {failed_component}. "
        "Because {failed_component} is {failure_description}, the dependency chain is broken "
        "and {service} may be affected."
    ),
    ("indirect", True, False): (
        "{service} depends on {intermediate_chain}, which depends on {failed_component}. "
        "Because {failed_component} is {failure_description}, the dependency chain is broken. "
        "Alternative inbound path detected from {alt_path}. "
        "Operational equivalence has not been verified — engineer review recommended."
    ),
    ("indirect", False, True): (
        "{service} depends on {intermediate_chain}, which depends on {failed_component}. "
        "Because {failed_component} is {failure_description}, the dependency chain is broken "
        "and {service} may be affected. "
        "{dq_warning}"
    ),
    ("indirect", True, True): (
        "{service} depends on {intermediate_chain}, which depends on {failed_component}. "
        "Because {failed_component} is {failure_description}, the dependency chain is broken. "
        "Alternative inbound path detected from {alt_path}. "
        "Operational equivalence has not been verified — engineer review recommended. "
        "{dq_warning}"
    ),
}

# ---------------------------------------------------------------------------
# DQ warning template
# ---------------------------------------------------------------------------

DQ_WARNING_TEMPLATE = (
    "dependency data quality for {component_name} is low "
    "(score: {score}) — impact conclusions for this path may be incomplete."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render_path(path_steps: list[dict]) -> str:
    """Join component names with ' → ' separator."""
    return " → ".join(step.get("component_name", "") for step in path_steps)


def build_explanation(
    affected_component_name: str,
    failed_component_name: str,
    failure_type: str,
    path_steps: list[dict],
    alternative_paths: list[list[dict]],
    low_dq_components: list[dict],
) -> str:
    """
    Build a human-readable explanation for an impact path.

    Args:
        affected_component_name : name of the affected service
        failed_component_name   : name of the failed component
        failure_type            : one of the FailureType enum values
        path_steps              : list of {component_name, ...} from failed to affected
        alternative_paths       : list of alternative path step lists
        low_dq_components       : list of {name, data_quality_score} for DQ warnings

    Returns:
        A formatted explanation string.
    """
    # hop_count: path includes failed node as step 0
    hop_count = len(path_steps) - 1 if path_steps else 0
    impact_type = "direct" if hop_count <= 1 else "indirect"
    has_alternative = len(alternative_paths) > 0
    has_dq_warning = len(low_dq_components) > 0

    template = TEMPLATES.get(
        (impact_type, has_alternative, has_dq_warning),
        TEMPLATES[("direct", False, False)],
    )

    failure_description = FAILURE_DESCRIPTIONS.get(failure_type, failure_type)

    # Build intermediate chain (all steps between failed_node and affected, exclusive)
    intermediate_names = [
        s.get("component_name", "") for s in path_steps[1:-1]
        if s.get("component_name", "")
    ]
    intermediate_chain = " → ".join(intermediate_names) if intermediate_names else failed_component_name

    # Build alt path string
    alt_path_str = "; ".join(
        render_path(ap) or "(unknown path)" for ap in alternative_paths
    ) if alternative_paths else ""

    # Build DQ warning string
    dq_parts = [
        DQ_WARNING_TEMPLATE.format(
            component_name=c.get("name", "unknown"),
            score=c.get("data_quality_score", "?"),
        )
        for c in low_dq_components
    ]
    dq_warning_str = " ".join(dq_parts)

    try:
        return template.format(
            service=affected_component_name,
            failed_component=failed_component_name,
            failure_description=failure_description,
            intermediate_chain=intermediate_chain,
            alt_path=alt_path_str,
            dq_warning=dq_warning_str,
        )
    except KeyError:
        # Fallback: produce a minimal explanation if template substitution fails
        return (
            f"{affected_component_name} may be affected because "
            f"{failed_component_name} is {failure_description}."
        )
