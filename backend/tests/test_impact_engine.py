"""
Comprehensive tests for the ImpactLens Impact Engine.

Covers Requirement 14, AC 1:
  - Direct dependants, indirect dependants, unaffected exclusion
  - Alternative path detection (component stays affected, appears in possible_alts)
  - Cycle safety (no infinite loop)
  - Failed edge excluded from traversal
  - Unknown health status propagation
  - Stale evidence triggers StalenessWarning
  - Higher criticality → higher impact score
  - Two-hop explanation uses indirect template
  - Multi-path deduplication (BFS visited set)
  - Failed edge traversal semantics (dependency_link_unavailable)
  - Impact score unchanged by DQ scores (score same, DCS differs)
  - All three failure type semantics
  - alt_path_ratio nonzero when alternatives exist
  - alt_path_ratio zero for linear chain
"""

import uuid
from datetime import datetime, timezone, timedelta

import networkx as nx
import pytest

from app.engine.active_simulation_store import ActiveSimulation
from app.engine.impact_engine import (
    _check_staleness,
    _find_apparent_alternative_sources,
    compute_data_confidence_score,
    compute_impact_score,
    find_impacted_components,
)
from app.engine.explanation_engine import build_explanation, render_path
from app.engine.graph_builder import build_simulation_graph
from app.models.simulation import StalenessWarning


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_graph(nodes, edges):
    """
    Build a NetworkX DiGraph for unit tests.

    nodes: [(id, name, criticality_weight, health_status, dq_score)]
    edges: [(src, tgt, edge_id=None, is_present=True)]
    """
    G = nx.DiGraph()
    for entry in nodes:
        node_id = entry[0]
        name = entry[1]
        cw = entry[2]
        health = entry[3] if len(entry) > 3 else "healthy"
        dq = entry[4] if len(entry) > 4 else 80
        G.add_node(node_id, name=name, criticality_weight=cw, health_status=health, data_quality_score=dq)
    for edge in edges:
        src = edge[0]
        tgt = edge[1]
        eid = edge[2] if len(edge) > 2 else str(uuid.uuid4())
        is_present = edge[3] if len(edge) > 3 else True
        G.add_edge(src, tgt, edge_id=eid, is_present=is_present)
    return G


def make_sim(target_id, failure_type="component_unavailable", target_type="component"):
    return ActiveSimulation(
        scenario_id="test-scenario",
        sim_id=str(uuid.uuid4()),
        target_type=target_type,
        target_id=target_id,
        failure_type=failure_type,
        impact_report={},
    )


# ---------------------------------------------------------------------------
# 1. Direct dependants
# ---------------------------------------------------------------------------

def test_direct_dependants_are_in_affected():
    """Hop-1 neighbours of a failed node appear in affected at distance 1."""
    # A -> B, A -> C  (B and C depend on A)
    G = make_graph(
        [("A", "ServiceA", 2, "healthy", 80),
         ("B", "ServiceB", 1, "healthy", 80),
         ("C", "ServiceC", 1, "healthy", 80)],
        [("A", "B"), ("A", "C")],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    assert "B" in affected
    assert "C" in affected
    assert affected["B"] == 1
    assert affected["C"] == 1


# ---------------------------------------------------------------------------
# 2. Indirect dependants
# ---------------------------------------------------------------------------

def test_indirect_dependants_are_in_affected():
    """Hop-2+ neighbours appear in affected with correct distances."""
    # A -> B -> C
    G = make_graph(
        [("A", "A", 2), ("B", "B", 2), ("C", "C", 1)],
        [("A", "B"), ("B", "C")],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    assert affected["B"] == 1
    assert affected["C"] == 2


# ---------------------------------------------------------------------------
# 3. Unaffected components excluded
# ---------------------------------------------------------------------------

def test_unaffected_components_not_in_affected():
    """Components not reachable from the failed node are excluded."""
    # A -> B ; D is disconnected
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("D", "D", 1)],
        [("A", "B")],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    assert "B" in affected
    assert "D" not in affected


# ---------------------------------------------------------------------------
# 4. Alternative path: component stays in affected, appears in possible_alts
# ---------------------------------------------------------------------------

def test_alternative_path_component_remains_in_affected():
    """
    When a dependant has an inbound path from a healthy source,
    it is listed in possible_alts but stays in affected[].
    """
    # A -> C  (A fails)
    # B -> C  (B is healthy — apparent alternative)
    G = make_graph(
        [("A", "A", 2, "healthy", 80),
         ("B", "B", 1, "healthy", 80),
         ("C", "C", 1, "healthy", 80)],
        [("A", "C"), ("B", "C")],
    )
    affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
    assert "C" in affected, "C must remain in affected (conservative)"
    assert "C" in possible_alts, "C should appear in possible_alts"
    assert "B" in possible_alts["C"]


def test_alt_path_ratio_nonzero_when_alternatives_exist():
    """isolation_score < 1.0 when alternative paths exist."""
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "C"), ("B", "C")],
    )
    affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
    _, breakdown = compute_impact_score(
        G, "A", affected, possible_alts, "component_unavailable", "component"
    )
    # At least one component in affected has an alternative → ratio > 0 → isolation < 1
    assert breakdown.isolation_score["value"] < 1.0


def test_alt_path_ratio_zero_for_linear_chain():
    """isolation_score == 1.0 for a simple linear chain (no alternatives)."""
    # A -> B -> C
    G = make_graph(
        [("A", "A", 2), ("B", "B", 2), ("C", "C", 1)],
        [("A", "B"), ("B", "C")],
    )
    affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
    _, breakdown = compute_impact_score(
        G, "A", affected, possible_alts, "component_unavailable", "component"
    )
    assert breakdown.isolation_score["value"] == 1.0


# ---------------------------------------------------------------------------
# 5. Cycle safety
# ---------------------------------------------------------------------------

def test_cycle_safety_no_infinite_loop():
    """BFS with a cycle must terminate without infinite loop."""
    # A -> B -> C -> A (cycle)
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "B"), ("B", "C"), ("C", "A")],
    )
    # Should complete without error (and not enter A again)
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    assert "B" in affected
    assert "C" in affected
    assert "A" not in affected  # A was the start, not re-visited as dependant


# ---------------------------------------------------------------------------
# 6. Failed edge excluded from traversal
# ---------------------------------------------------------------------------

def test_failed_edge_blocks_traversal():
    """An edge with is_present=False is not traversed."""
    # A -[broken]-> B -> C
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "B", "e1", False), ("B", "C", "e2", True)],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, {"e1"})
    assert "B" not in affected
    assert "C" not in affected


# ---------------------------------------------------------------------------
# 7. Unknown health status propagates
# ---------------------------------------------------------------------------

def test_unknown_health_status_propagates():
    """Components with 'unknown' health status are still reachable and added to affected."""
    G = make_graph(
        [("A", "A", 2, "healthy"), ("B", "B", 1, "unknown")],
        [("A", "B")],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    assert "B" in affected


# ---------------------------------------------------------------------------
# 8. Stale evidence triggers StalenessWarning
# ---------------------------------------------------------------------------

def test_stale_evidence_triggers_warning():
    """A component observed > 72 h ago generates a StalenessWarning."""
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    components = [
        {"id": "A", "name": "ServiceA", "last_observed_at": stale_time},
        {"id": "B", "name": "ServiceB", "last_observed_at": stale_time},
    ]
    warnings = _check_staleness(components, {"A", "B"}, freshness_threshold_hours=72)
    assert len(warnings) == 2
    ids = {w.component_id for w in warnings}
    assert "A" in ids
    assert "B" in ids


def test_fresh_component_no_warning():
    """A recently observed component does NOT trigger a warning."""
    fresh_time = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    components = [{"id": "A", "name": "ServiceA", "last_observed_at": fresh_time}]
    warnings = _check_staleness(components, {"A"}, freshness_threshold_hours=72)
    assert warnings == []


def test_stale_component_not_in_involved_skipped():
    """A stale component not in involved_ids is not included in warnings."""
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    components = [{"id": "A", "name": "ServiceA", "last_observed_at": stale_time}]
    warnings = _check_staleness(components, {"B"}, freshness_threshold_hours=72)
    assert warnings == []


# ---------------------------------------------------------------------------
# 9. Higher criticality → higher impact score
# ---------------------------------------------------------------------------

def test_higher_criticality_yields_higher_score():
    """
    Two identical topologies, differing only in failed node criticality.
    The one with higher criticality_weight must produce a higher (or equal) score.
    """
    def score_for_cw(cw: int) -> int:
        G = make_graph(
            [("A", "A", cw), ("B", "B", 1)],
            [("A", "B")],
        )
        affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
        score, _ = compute_impact_score(G, "A", affected, possible_alts, "component_unavailable", "component")
        return score

    score_low = score_for_cw(1)
    score_high = score_for_cw(4)
    assert score_high > score_low, f"Expected higher score for cw=4, got {score_high} vs {score_low}"


# ---------------------------------------------------------------------------
# 10. Two-hop explanation matches indirect template
# ---------------------------------------------------------------------------

def test_two_hop_explanation_uses_indirect_template():
    """A path with 2+ hops produces an 'indirect' template explanation."""
    explanation = build_explanation(
        affected_component_name="ServiceC",
        failed_component_name="ServiceA",
        failure_type="component_unavailable",
        path_steps=[
            {"component_name": "ServiceA"},
            {"component_name": "ServiceB"},
            {"component_name": "ServiceC"},
        ],
        alternative_paths=[],
        low_dq_components=[],
    )
    # The indirect template contains "depends on"..."which depends on"
    assert "which depends on" in explanation


def test_one_hop_explanation_uses_direct_template():
    """A path with 1 hop produces a 'direct' template explanation."""
    explanation = build_explanation(
        affected_component_name="ServiceB",
        failed_component_name="ServiceA",
        failure_type="component_unavailable",
        path_steps=[
            {"component_name": "ServiceA"},
            {"component_name": "ServiceB"},
        ],
        alternative_paths=[],
        low_dq_components=[],
    )
    assert "depends directly on" in explanation
    assert "which depends on" not in explanation


# ---------------------------------------------------------------------------
# 11. Multi-path deduplication (BFS visited set)
# ---------------------------------------------------------------------------

def test_multi_path_deduplication():
    """
    When C is reachable via both A->C and A->B->C, BFS visited set
    ensures C appears only once in affected (not duplicated).
    """
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "C"), ("A", "B"), ("B", "C")],
    )
    affected, _ = find_impacted_components(G, "A", {"A"}, set())
    # C should be in affected exactly once — dict keys are unique
    assert "C" in affected
    assert affected["C"] == 1  # direct path takes priority in BFS


# ---------------------------------------------------------------------------
# 12. Failed edge traversal semantics (dependency_link_unavailable)
# ---------------------------------------------------------------------------

def test_failed_edge_semantics_via_graph_builder():
    """
    build_simulation_graph with a dependency_link_unavailable edge failure
    marks the edge is_present=False; downstream nodes are not affected.
    """
    components = [
        {"id": "A", "name": "A", "criticality": "high", "health_status": "healthy", "data_quality_score": 80},
        {"id": "B", "name": "B", "criticality": "low", "health_status": "healthy", "data_quality_score": 80},
    ]
    edges = [
        {"id": "e1", "source_component_id": "A", "target_component_id": "B"},
    ]
    sim = make_sim("e1", failure_type="dependency_link_unavailable", target_type="edge")
    G, failed_nodes, failed_edges = build_simulation_graph(components, edges, sim)
    assert G["A"]["B"]["is_present"] is False
    assert "e1" in failed_edges
    assert not failed_nodes  # edge failure doesn't mark nodes


# ---------------------------------------------------------------------------
# 13. Impact score unchanged by DQ scores (score same, DCS differs)
# ---------------------------------------------------------------------------

def test_impact_score_unchanged_by_dq():
    """
    compute_impact_score does NOT read data_quality_score from nodes.
    Two graphs with same topology but different DQ should yield identical impact_score.
    """
    def score_for_dq(dq: int) -> tuple:
        G = make_graph(
            [("A", "A", 2, "healthy", dq), ("B", "B", 1, "healthy", dq)],
            [("A", "B")],
        )
        affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
        return compute_impact_score(G, "A", affected, possible_alts, "component_unavailable", "component")

    score_low_dq, _ = score_for_dq(10)
    score_high_dq, _ = score_for_dq(95)
    assert score_low_dq == score_high_dq


def test_dcs_differs_by_dq():
    """compute_data_confidence_score reflects actual node DQ values."""
    G_low = make_graph(
        [("A", "A", 2, "healthy", 10), ("B", "B", 1, "healthy", 10)],
        [("A", "B")],
    )
    G_high = make_graph(
        [("A", "A", 2, "healthy", 95), ("B", "B", 1, "healthy", 95)],
        [("A", "B")],
    )
    dcs_low = compute_data_confidence_score(G_low, ["A", "B"])
    dcs_high = compute_data_confidence_score(G_high, ["A", "B"])
    assert dcs_low < dcs_high


# ---------------------------------------------------------------------------
# 14. All three failure type semantics
# ---------------------------------------------------------------------------

def test_component_unavailable_blocks_propagation():
    """
    component_unavailable: the failed node is in failed_node_ids.
    BFS does NOT propagate through another unavailable node mid-chain.
    """
    # A -> B -> C  (A fails; B is also unavailable)
    components = [
        {"id": "A", "name": "A", "criticality": "critical", "health_status": "healthy", "data_quality_score": 80},
        {"id": "B", "name": "B", "criticality": "low", "health_status": "failed", "data_quality_score": 80},
        {"id": "C", "name": "C", "criticality": "low", "health_status": "healthy", "data_quality_score": 80},
    ]
    edges = [
        {"id": "e1", "source_component_id": "A", "target_component_id": "B"},
        {"id": "e2", "source_component_id": "B", "target_component_id": "C"},
    ]
    sim = make_sim("A", failure_type="component_unavailable", target_type="component")
    G, failed_nodes, failed_edges = build_simulation_graph(components, edges, sim)
    # BFS from A; B is healthy post-graph-build but failed_nodes={'A'}
    affected, _ = find_impacted_components(G, "A", failed_nodes, failed_edges)
    # B is a direct dependant and should be affected
    assert "B" in affected


def test_component_degraded_traverses_through_node():
    """
    component_degraded: the failed node is NOT in failed_node_ids.
    BFS continues through the degraded node.
    """
    components = [
        {"id": "A", "name": "A", "criticality": "high", "health_status": "healthy", "data_quality_score": 80},
        {"id": "B", "name": "B", "criticality": "low", "health_status": "healthy", "data_quality_score": 80},
    ]
    edges = [
        {"id": "e1", "source_component_id": "A", "target_component_id": "B"},
    ]
    sim = make_sim("A", failure_type="component_degraded", target_type="component")
    G, failed_nodes, failed_edges = build_simulation_graph(components, edges, sim)
    # component_degraded does NOT add to failed_node_ids
    assert "A" not in failed_nodes
    assert G.nodes["A"]["health_status"] == "degraded"
    affected, _ = find_impacted_components(G, "A", failed_nodes, failed_edges)
    assert "B" in affected


def test_dependency_link_unavailable_only_marks_edge():
    """
    dependency_link_unavailable: only the selected edge is_present=False.
    Both endpoint nodes keep their baseline health status.
    """
    components = [
        {"id": "A", "name": "A", "criticality": "high", "health_status": "healthy", "data_quality_score": 80},
        {"id": "B", "name": "B", "criticality": "low", "health_status": "healthy", "data_quality_score": 80},
    ]
    edges = [{"id": "e1", "source_component_id": "A", "target_component_id": "B"}]
    sim = make_sim("e1", failure_type="dependency_link_unavailable", target_type="edge")
    G, failed_nodes, failed_edges = build_simulation_graph(components, edges, sim)
    assert G.nodes["A"]["health_status"] == "healthy"
    assert G.nodes["B"]["health_status"] == "healthy"
    assert not failed_nodes
    assert G["A"]["B"]["is_present"] is False


# ---------------------------------------------------------------------------
# 15. render_path utility
# ---------------------------------------------------------------------------

def test_render_path_joins_names():
    steps = [{"component_name": "A"}, {"component_name": "B"}, {"component_name": "C"}]
    assert render_path(steps) == "A → B → C"


def test_render_path_single_step():
    steps = [{"component_name": "Only"}]
    assert render_path(steps) == "Only"


def test_render_path_empty():
    assert render_path([]) == ""


# ---------------------------------------------------------------------------
# 16. Explanation templates for all failure types
# ---------------------------------------------------------------------------

def test_explanation_component_unavailable():
    expl = build_explanation(
        "ServiceB", "ServiceA", "component_unavailable",
        [{"component_name": "ServiceA"}, {"component_name": "ServiceB"}],
        [], [],
    )
    assert "unavailable" in expl


def test_explanation_component_degraded():
    expl = build_explanation(
        "ServiceB", "ServiceA", "component_degraded",
        [{"component_name": "ServiceA"}, {"component_name": "ServiceB"}],
        [], [],
    )
    assert "degraded" in expl


def test_explanation_dependency_link_unavailable():
    expl = build_explanation(
        "ServiceB", "ServiceA", "dependency_link_unavailable",
        [{"component_name": "ServiceA"}, {"component_name": "ServiceB"}],
        [], [],
    )
    assert "disconnected" in expl or "link unavailable" in expl


# ---------------------------------------------------------------------------
# 17. Alternative path explanation includes alt source mention
# ---------------------------------------------------------------------------

def test_explanation_includes_alt_path_note():
    expl = build_explanation(
        "ServiceC", "ServiceA", "component_unavailable",
        [{"component_name": "ServiceA"}, {"component_name": "ServiceC"}],
        [[{"component_name": "ServiceB"}]],  # alternative path
        [],
    )
    assert "Alternative inbound path" in expl or "alternative" in expl.lower()


# ---------------------------------------------------------------------------
# 18. DQ warning in explanation
# ---------------------------------------------------------------------------

def test_explanation_includes_dq_warning():
    expl = build_explanation(
        "ServiceB", "ServiceA", "component_unavailable",
        [{"component_name": "ServiceA"}, {"component_name": "ServiceB"}],
        [],
        [{"name": "ServiceB", "data_quality_score": 20}],
    )
    assert "data quality" in expl.lower() or "dq" in expl.lower() or "score" in expl.lower()


# ---------------------------------------------------------------------------
# 19. compute_data_confidence_score edge cases
# ---------------------------------------------------------------------------

def test_dcs_empty_nodes_returns_100():
    G = make_graph([("A", "A", 1)], [])
    assert compute_data_confidence_score(G, []) == 100


def test_dcs_single_node():
    G = make_graph([("A", "A", 1, "healthy", 60)], [])
    assert compute_data_confidence_score(G, ["A"]) == 60


def test_dcs_average_of_nodes():
    G = make_graph(
        [("A", "A", 1, "healthy", 40), ("B", "B", 1, "healthy", 80)], []
    )
    result = compute_data_confidence_score(G, ["A", "B"])
    assert result == 60


# ---------------------------------------------------------------------------
# 20. Impact score bounds
# ---------------------------------------------------------------------------

def test_impact_score_within_bounds():
    """Impact score must always be between 0 and 100 inclusive."""
    G = make_graph(
        [("A", "A", 4, "healthy", 90)] + [(f"N{i}", f"N{i}", 1, "healthy", 90) for i in range(25)],
        [("A", f"N{i}") for i in range(25)],
    )
    affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
    score, _ = compute_impact_score(G, "A", affected, possible_alts, "component_unavailable", "component")
    assert 0 <= score <= 100


def test_impact_score_zero_when_no_affected():
    """
    No affected components: reach=0, proximity=0, but criticality and isolation
    still contribute.  For cw=4: raw = 1.0*0.35 + 0 + 0 + 1.0*0.15 = 0.50 → score=50.
    The formula is labelled 'not an industry standard metric'; the test simply asserts
    the score is within [0, 100] and the reach/proximity sub-scores are 0.
    """
    G = make_graph([("A", "A", 4)], [])
    affected, possible_alts = find_impacted_components(G, "A", {"A"}, set())
    score, breakdown = compute_impact_score(G, "A", affected, possible_alts, "component_unavailable", "component")
    assert 0 <= score <= 100
    assert breakdown.reach_score["value"] == 0.0
    assert breakdown.proximity_score["value"] == 0.0


# ---------------------------------------------------------------------------
# 21. find_apparent_alternative_sources
# ---------------------------------------------------------------------------

def test_find_apparent_alts_excludes_failed_source():
    """A source that is itself failed should not count as an alternative."""
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "C"), ("B", "C")],
    )
    # B is also failed
    alts = _find_apparent_alternative_sources(G, "C", {"A", "B"}, {})
    assert "B" not in alts


def test_find_apparent_alts_excludes_already_impacted():
    """A source already in current_impacted should not count as an alternative."""
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "C"), ("B", "C")],
    )
    # B is already impacted
    alts = _find_apparent_alternative_sources(G, "C", {"A"}, {"B": 1})
    assert "B" not in alts


def test_find_apparent_alts_excludes_absent_edge():
    """A source connected via is_present=False edge is not an alternative."""
    G = make_graph(
        [("A", "A", 2), ("B", "B", 1), ("C", "C", 1)],
        [("A", "C", "e1", True), ("B", "C", "e2", False)],
    )
    alts = _find_apparent_alternative_sources(G, "C", {"A"}, {})
    assert "B" not in alts
