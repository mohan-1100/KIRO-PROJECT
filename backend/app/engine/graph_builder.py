"""
Graph builder for ImpactLens simulation engine.

Converts DB records (components + edges) into a NetworkX DiGraph and
applies the simulation overlay (failed node or failed edge) on top of
the baseline graph.

Edge direction convention: A → B means B depends on A.
  - source_component_id = A (the dependency being depended on)
  - target_component_id = B (the component that depends on A)

If A fails, we traverse successors of A to find all affected components.
"""

from typing import Optional

import networkx as nx

from app.engine.active_simulation_store import ActiveSimulation
from app.models.common import CRITICALITY_WEIGHTS


def build_simulation_graph(
    components: list[dict],
    edges: list[dict],
    active_sim: Optional[ActiveSimulation],
) -> tuple[nx.DiGraph, set[str], set[str]]:
    """
    Build a NetworkX DiGraph from scenario components and edges, then apply
    the simulation overlay.

    Returns:
        G               : DiGraph with node/edge attributes set
        failed_node_ids : set of component IDs treated as failed (component_unavailable only)
        failed_edge_ids : set of edge IDs treated as absent (dependency_link_unavailable only)

    Node attributes:
        name               : component name (str)
        criticality_weight : integer 1–4 from CRITICALITY_WEIGHTS
        health_status      : baseline health_status string (may be overridden by overlay)
        data_quality_score : integer 0–100

    Edge attributes:
        edge_id    : the DB edge UUID
        is_present : True (baseline) or False (failed via dependency_link_unavailable)
    """
    G = nx.DiGraph()

    # Step 1: Add all nodes
    for comp in components:
        G.add_node(
            comp["id"],
            name=comp["name"],
            criticality_weight=CRITICALITY_WEIGHTS.get(comp.get("criticality", "low"), 1),
            health_status=comp.get("health_status", "unknown"),
            data_quality_score=comp.get("data_quality_score", 50),
        )

    # Step 2: Add all edges with is_present=True
    for edge in edges:
        G.add_edge(
            edge["source_component_id"],
            edge["target_component_id"],
            edge_id=edge["id"],
            is_present=True,
        )

    failed_node_ids: set[str] = set()
    failed_edge_ids: set[str] = set()

    # Step 3: Apply simulation overlay
    if active_sim is None:
        return G, failed_node_ids, failed_edge_ids

    if active_sim.target_type == "component":
        target_id = active_sim.target_id
        if target_id in G:
            if active_sim.failure_type == "component_unavailable":
                # Mark node as failed; BFS will NOT propagate through it.
                failed_node_ids.add(target_id)
                G.nodes[target_id]["health_status"] = "failed"

            elif active_sim.failure_type == "component_degraded":
                # Mark node as degraded; edges REMAIN traversable.
                # Do NOT add to failed_node_ids — BFS continues through degraded nodes.
                G.nodes[target_id]["health_status"] = "degraded"

    elif active_sim.target_type == "edge":
        # dependency_link_unavailable: mark only the selected edge as absent.
        # Both endpoint nodes keep their baseline health_status.
        target_edge_id = active_sim.target_id
        failed_edge_ids.add(target_edge_id)
        for u, v, data in G.edges(data=True):
            if data.get("edge_id") == target_edge_id:
                G[u][v]["is_present"] = False
                break

    return G, failed_node_ids, failed_edge_ids
