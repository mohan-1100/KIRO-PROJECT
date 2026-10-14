"""
ImpactLens Impact Engine.

Implements BFS traversal from a failed component or edge, computes the
Impact Score (4-factor ImpactLens heuristic v1.0), Data Confidence Score,
and assembles a complete ImpactReport.

Graph convention: A → B means B depends on A.
  Traversal follows successors of the failed node.
  A node is "affected" if it is reachable from the failed node via the
  dependant direction and has no valid apparent alternative source.

Alternative path detection (conservative):
  A component D is checked for apparent alternatives when first encountered.
  If at least one inbound edge to D comes from a non-failed, non-impacted
  source, D's possible alternatives are recorded but D REMAINS in affected[].
  Topology alone does not prove operational equivalence.
"""

import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import networkx as nx

from app.engine.active_simulation_store import ActiveSimulation
from app.engine.graph_builder import build_simulation_graph
from app.models.common import CRITICALITY_WEIGHTS
from app.models.simulation import (
    AffectedComponentSummary,
    ImpactPath,
    ImpactReport,
    PathStep,
    PossibleAltPathComponent,
    ScoreBreakdown,
    StalenessWarning,
)


# ---------------------------------------------------------------------------
# Alternative path detection
# ---------------------------------------------------------------------------

def _find_apparent_alternative_sources(
    G: nx.DiGraph,
    dependant: str,
    failed_node_ids: set[str],
    current_impacted: dict[str, int],
) -> list[str]:
    """
    Return source IDs that appear to provide an alternative inbound path
    to 'dependant' based on graph topology only.

    A source qualifies if:
      (a) The edge source→dependant is present (is_present=True).
      (b) The source is NOT a failed node (component_unavailable).
      (c) The source is NOT already in current_impacted.

    Returns an empty list if no valid alternative sources exist.
    Returns a non-empty list if topology suggests an alternative —
    this does NOT mean the service can operate without the failed dependency.
    Engineers must verify operational equivalence separately.
    """
    alternatives: list[str] = []
    for source in G.predecessors(dependant):
        edge_data = G[source][dependant]
        # (a) Edge must be present
        if not edge_data.get("is_present", True):
            continue
        # (b) Source must not be failed
        if source in failed_node_ids:
            continue
        # (c) Source must not be in impacted set
        if source in current_impacted:
            continue
        alternatives.append(source)
    return alternatives


# ---------------------------------------------------------------------------
# BFS traversal
# ---------------------------------------------------------------------------

def find_impacted_components(
    G: nx.DiGraph,
    failed_node: str,
    failed_node_ids: set[str],
    failed_edge_ids: set[str],
) -> tuple[dict[str, int], dict[str, list[str]]]:
    """
    BFS from failed_node following dependant edges.

    Returns:
        affected      : {component_id: hop_distance} — all impacted components
        possible_alts : {component_id: [alt_source_id, ...]} — components in
                        affected[] that have apparent alternative inbound paths

    Design: a component with an apparent alternative is still included in
    affected[] (conservative). The alternative is surfaced as a disclosure
    notice, not as proof of service continuity.

    Cycle safety: visited set prevents reprocessing.
    Failed edges: is_present=False edges are skipped.
    Failed nodes: propagation stops at failed nodes in failed_node_ids.
    """
    affected: dict[str, int] = {}
    possible_alts: dict[str, list[str]] = {}
    visited: set[str] = {failed_node}
    queue: deque[tuple[str, int]] = deque([(failed_node, 0)])

    while queue:
        current, hop = queue.popleft()

        for successor in G.successors(current):
            edge_data = G[current][successor]

            # Skip failed edges (dependency_link_unavailable)
            if not edge_data.get("is_present", True):
                continue

            # Do not propagate through a component_unavailable node
            # (block propagation when current is failed, UNLESS current is the start node)
            if current in failed_node_ids and current != failed_node:
                continue

            if successor in visited:
                continue
            visited.add(successor)

            # Detect apparent alternative sources (topology only)
            alts = _find_apparent_alternative_sources(
                G, successor, failed_node_ids, affected
            )
            if alts:
                possible_alts[successor] = alts

            hop_distance = hop + 1
            affected[successor] = hop_distance
            queue.append((successor, hop_distance))

    return affected, possible_alts


# ---------------------------------------------------------------------------
# Impact Score computation
# ---------------------------------------------------------------------------

def compute_impact_score(
    G: nx.DiGraph,
    failed_node: str,
    affected: dict[str, int],
    possible_alts: dict[str, list[str]],
    failure_type: str,
    target_type: str,
    failed_edge_source: Optional[str] = None,
    failed_edge_target: Optional[str] = None,
) -> tuple[int, ScoreBreakdown]:
    """
    Compute the ImpactLens heuristic Impact Score (0–100).

    Formula (v1.0):
      criticality_score = criticality_weight / 4
      reach_score       = min(affected_count, 20) / 20
      proximity_score   = 1 / (1 + avg_hop_distance)   (0 if no affected)
      isolation_score   = 1 − alt_path_ratio
        where alt_path_ratio = count(affected with possible_alts) / affected_count

      raw_score = criticality*0.35 + reach*0.30 + proximity*0.20 + isolation*0.15
      impact_score = min(100, round(raw_score * 100))

    For edge failures, criticality_score uses max(source, target) criticality.

    This formula is labelled:
      "ImpactLens heuristic v1.0 — not an industry standard metric"
    """
    affected_count = len(affected)

    # criticality_score
    if target_type == "edge" and failed_edge_source and failed_edge_target:
        cw_src = G.nodes[failed_edge_source].get("criticality_weight", 1) if failed_edge_source in G else 1
        cw_tgt = G.nodes[failed_edge_target].get("criticality_weight", 1) if failed_edge_target in G else 1
        crit_weight = max(cw_src, cw_tgt)
    else:
        crit_weight = G.nodes[failed_node].get("criticality_weight", 1) if failed_node in G else 1

    criticality_score = crit_weight / 4.0

    # reach_score
    reach_score = min(affected_count, 20) / 20.0 if affected_count > 0 else 0.0

    # proximity_score
    if affected_count > 0:
        avg_hop = sum(affected.values()) / affected_count
        proximity_score = 1.0 / (1.0 + avg_hop)
    else:
        proximity_score = 0.0

    # isolation_score — computed from possible_alts
    alt_path_count = sum(1 for nid in affected if possible_alts.get(nid))
    alt_path_ratio = alt_path_count / affected_count if affected_count > 0 else 0.0
    isolation_score = 1.0 - alt_path_ratio

    raw_score = (
        criticality_score * 0.35
        + reach_score * 0.30
        + proximity_score * 0.20
        + isolation_score * 0.15
    )
    impact_score = min(100, round(raw_score * 100))

    breakdown = ScoreBreakdown(
        label="ImpactLens heuristic v1.0 — not an industry standard metric",
        criticality_score={"value": round(criticality_score, 4), "weight": 0.35},
        reach_score={"value": round(reach_score, 4), "weight": 0.30},
        proximity_score={"value": round(proximity_score, 4), "weight": 0.20},
        isolation_score={"value": round(isolation_score, 4), "weight": 0.15},
    )
    return impact_score, breakdown


def compute_data_confidence_score(
    G: nx.DiGraph,
    involved_node_ids: list[str],
) -> int:
    """
    Compute the Data Confidence Score as the arithmetic mean of
    data_quality_score for all involved nodes, rounded to nearest int.
    Returns 100 if no nodes are involved.

    This score is INDEPENDENT of the Impact Score and does not modify it.
    """
    if not involved_node_ids:
        return 100
    scores = [
        G.nodes[nid].get("data_quality_score", 50)
        for nid in involved_node_ids
        if nid in G
    ]
    if not scores:
        return 100
    return round(sum(scores) / len(scores))


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------

def _check_staleness(
    components: list[dict],
    involved_ids: set[str],
    freshness_threshold_hours: int,
) -> list[StalenessWarning]:
    """Return staleness warnings for involved components with stale last_observed_at."""
    warnings: list[StalenessWarning] = []
    now = datetime.now(timezone.utc)
    for comp in components:
        if comp["id"] not in involved_ids:
            continue
        last_obs = comp.get("last_observed_at")
        if not last_obs:
            continue
        try:
            obs_dt = datetime.fromisoformat(last_obs.replace("Z", "+00:00"))
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
            elapsed_hours = (now - obs_dt).total_seconds() / 3600.0
            if elapsed_hours > freshness_threshold_hours:
                warnings.append(StalenessWarning(
                    component_id=comp["id"],
                    component_name=comp["name"],
                    hours_since_observed=round(elapsed_hours, 1),
                ))
        except (ValueError, TypeError):
            pass
    return warnings


# ---------------------------------------------------------------------------
# Impact path reconstruction
# ---------------------------------------------------------------------------

def _reconstruct_paths(
    G: nx.DiGraph,
    failed_node: str,
    affected: dict[str, int],
    failed_node_ids: set[str],
) -> dict[str, list[str]]:
    """
    For each affected node, find one shortest path from failed_node using BFS.
    Returns {component_id: [node_id, ...]} in order from failed_node to component.
    """
    paths: dict[str, list[str]] = {}
    try:
        for target in affected:
            try:
                # Build a subgraph without failed edges for path finding
                path = nx.shortest_path(G, source=failed_node, target=target)
                paths[target] = path
            except nx.NetworkXNoPath:
                pass
    except Exception:
        pass
    return paths


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def build_impact_report(
    components: list[dict],
    edges: list[dict],
    active_sim: ActiveSimulation,
    freshness_threshold_hours: int = 72,
) -> ImpactReport:
    """
    Orchestrate the full impact analysis and return a populated ImpactReport.

    Steps:
      1. Build simulation graph with overlay
      2. Run BFS traversal
      3. Compute Impact Score and Data Confidence Score
      4. Check staleness
      5. Reconstruct impact paths
      6. Build per-component explanations
      7. Assemble ImpactReport
    """
    from app.engine.explanation_engine import build_explanation

    # Step 1 — Build graph
    G, failed_node_ids, failed_edge_ids = build_simulation_graph(
        components, edges, active_sim
    )

    # Determine the traversal start node
    if active_sim.target_type == "component":
        failed_node = active_sim.target_id
        failed_edge_source = None
        failed_edge_target = None
    else:
        # For edge failure, find the source node of the failed edge
        failed_edge_source = None
        failed_edge_target = None
        for u, v, data in G.edges(data=True):
            if data.get("edge_id") == active_sim.target_id:
                failed_edge_source = u
                failed_edge_target = v
                break
        failed_node = failed_edge_source or active_sim.target_id

    # Step 2 — BFS
    if failed_node not in G:
        # Target not found in graph — return empty report
        return ImpactReport(
            sim_id=active_sim.sim_id,
            scenario_id=active_sim.scenario_id,
            failed_target_id=active_sim.target_id,
            failed_target_type=active_sim.target_type,
            failure_type=active_sim.failure_type,
            impact_score=0,
            data_confidence_score=100,
            score_breakdown=ScoreBreakdown(
                criticality_score={"value": 0.0, "weight": 0.35},
                reach_score={"value": 0.0, "weight": 0.30},
                proximity_score={"value": 0.0, "weight": 0.20},
                isolation_score={"value": 1.0, "weight": 0.15},
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    affected, possible_alts = find_impacted_components(
        G, failed_node, failed_node_ids, failed_edge_ids
    )

    # Step 3 — Scores
    impact_score, breakdown = compute_impact_score(
        G, failed_node, affected, possible_alts,
        active_sim.failure_type, active_sim.target_type,
        failed_edge_source, failed_edge_target,
    )

    involved_ids = list(affected.keys())
    data_confidence_score = compute_data_confidence_score(G, involved_ids)

    # Step 4 — Staleness
    involved_set = set(involved_ids)
    staleness_warnings = _check_staleness(components, involved_set, freshness_threshold_hours)

    # Step 5 — Sort affected by severity contribution (desc), ties by name asc
    comp_map = {c["id"]: c for c in components}

    def severity_contribution(comp_id: str) -> float:
        cw = G.nodes[comp_id].get("criticality_weight", 1) if comp_id in G else 1
        has_alt = bool(possible_alts.get(comp_id))
        return cw * (0.0 if has_alt else 1.0)

    sorted_affected = sorted(
        affected.items(),
        key=lambda x: (-severity_contribution(x[0]), comp_map.get(x[0], {}).get("name", x[0])),
    )

    # Step 6 — Build AffectedComponentSummary lists
    directly_affected: list[AffectedComponentSummary] = []
    transitively_affected: list[AffectedComponentSummary] = []

    for comp_id, hop in sorted_affected:
        comp = comp_map.get(comp_id, {})
        alt_sources = possible_alts.get(comp_id, [])
        alt_source_names = [
            G.nodes[s].get("name", s) for s in alt_sources if s in G
        ]
        summary = AffectedComponentSummary(
            component_id=comp_id,
            name=comp.get("name", comp_id),
            criticality=comp.get("criticality", "low"),
            severity_contribution=severity_contribution(comp_id),
            has_alternative_path=bool(alt_sources),
            possible_alternative_sources=alt_source_names,
        )
        if hop == 1:
            directly_affected.append(summary)
        else:
            transitively_affected.append(summary)

    # Step 7 — Reconstruct paths and build explanations
    paths = _reconstruct_paths(G, failed_node, affected, failed_node_ids)
    failed_comp_name = G.nodes[failed_node].get("name", failed_node) if failed_node in G else failed_node

    impact_paths: list[ImpactPath] = []
    for comp_id, hop in sorted_affected:
        comp = comp_map.get(comp_id, {})
        comp_name = comp.get("name", comp_id)
        path_node_ids = paths.get(comp_id, [failed_node, comp_id])

        path_steps = [
            PathStep(
                component_id=node_id,
                component_name=G.nodes[node_id].get("name", node_id) if node_id in G else node_id,
                edge_direction="→" if i < len(path_node_ids) - 1 else None,
            )
            for i, node_id in enumerate(path_node_ids)
        ]

        low_dq_comps = [
            {
                "name": comp_map.get(nid, {}).get("name", nid),
                "data_quality_score": G.nodes[nid].get("data_quality_score", 50),
            }
            for nid in path_node_ids
            if nid in G and G.nodes[nid].get("data_quality_score", 50) < 50
        ]

        has_dq_warning = bool(low_dq_comps)

        alt_sources = possible_alts.get(comp_id, [])
        alt_paths_rendered = [
            [PathStep(component_id=s, component_name=G.nodes[s].get("name", s) if s in G else s)]
            for s in alt_sources
        ]

        explanation = build_explanation(
            affected_component_name=comp_name,
            failed_component_name=failed_comp_name,
            failure_type=active_sim.failure_type,
            path_steps=[{"component_name": ps.component_name} for ps in path_steps],
            alternative_paths=[
                [{"component_name": G.nodes[s].get("name", s) if s in G else s}]
                for s in alt_sources
            ],
            low_dq_components=low_dq_comps,
        )

        impact_paths.append(ImpactPath(
            affected_component_id=comp_id,
            affected_component_name=comp_name,
            path_steps=path_steps,
            explanation_text=explanation,
            has_dq_warning=has_dq_warning,
            alternative_paths=alt_paths_rendered,
        ))

    # Step 8 — possible_alt_path_components
    possible_alt_path_list: list[PossibleAltPathComponent] = []
    for comp_id, alt_sources in possible_alts.items():
        comp = comp_map.get(comp_id, {})
        possible_alt_path_list.append(PossibleAltPathComponent(
            component_id=comp_id,
            component_name=comp.get("name", comp_id),
            possible_alternative_source_names=[
                G.nodes[s].get("name", s) for s in alt_sources if s in G
            ],
        ))

    # already_failed_warning
    already_failed = False
    if active_sim.target_type == "component":
        target_comp = comp_map.get(active_sim.target_id, {})
        baseline_status = target_comp.get("health_status", "unknown")
        already_failed = (
            baseline_status == "failed"
            and active_sim.failure_type == "component_unavailable"
        )

    # low_confidence_notice
    low_confidence_notice = None
    if data_confidence_score < 50:
        low_confidence_notice = (
            "Data confidence is low — impact conclusions may be incomplete "
            "due to missing or stale dependency information."
        )

    return ImpactReport(
        sim_id=active_sim.sim_id,
        scenario_id=active_sim.scenario_id,
        failed_target_id=active_sim.target_id,
        failed_target_type=active_sim.target_type,
        failure_type=active_sim.failure_type,
        impact_score=impact_score,
        data_confidence_score=data_confidence_score,
        score_breakdown=breakdown,
        low_confidence_notice=low_confidence_notice,
        already_failed_warning=already_failed,
        directly_affected=directly_affected,
        transitively_affected=transitively_affected,
        impact_paths=impact_paths,
        possible_alt_path_components=possible_alt_path_list,
        staleness_warnings=staleness_warnings,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
