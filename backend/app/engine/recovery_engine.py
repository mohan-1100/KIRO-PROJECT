"""
ImpactLens Recovery Engine.

Computes projected recovery scenarios WITHOUT modifying the Active Simulation
or the baseline database. Works only on graph copies.

INVARIANT: This module never calls active_sim_store.set() or active_sim_store.clear().
           The original graph G passed in is never mutated.
"""
from typing import Optional
import networkx as nx

from app.engine.active_simulation_store import ActiveSimulation
from app.engine.impact_engine import (
    compute_impact_score,
    find_impacted_components,
)
from app.models.recovery import RecoveryOption


def compute_recovery_options(
    G: nx.DiGraph,
    active_sim: ActiveSimulation,
    original_impacted: dict[str, int],
    all_components: list[dict],
) -> list[RecoveryOption]:
    """
    Evaluate recovery candidates. Returns ranked RecoveryOption list.
    G and active_sim are read-only — never modified.
    """
    options: list[RecoveryOption] = []

    if active_sim.target_type == "component":
        options = _component_recovery(G, active_sim, original_impacted, all_components)
    elif active_sim.target_type == "edge":
        opt = _edge_recovery(G, active_sim, original_impacted)
        if opt:
            options.append(opt)

    options.sort(key=lambda o: o.services_recovered_count, reverse=True)
    return options


def _component_recovery(
    G: nx.DiGraph,
    active_sim: ActiveSimulation,
    original_impacted: dict[str, int],
    all_components: list[dict],
) -> list[RecoveryOption]:
    options: list[RecoveryOption] = []

    # Candidates: the simulation target + any other failed/degraded components
    candidates = [
        c for c in all_components
        if c["id"] == active_sim.target_id
        or c.get("health_status") in ("failed", "degraded")
    ]

    for candidate in candidates:
        G_copy = G.copy()
        cid = candidate["id"]
        if cid in G_copy:
            G_copy.nodes[cid]["health_status"] = "healthy"

        post_impacted, post_alts = find_impacted_components(
            G_copy,
            failed_node=active_sim.target_id,
            failed_node_ids=set(),
            failed_edge_ids=set(),
        )

        recovered = list(set(original_impacted.keys()) - set(post_impacted.keys()))
        still_affected = list(post_impacted.keys())

        projected_score, _ = compute_impact_score(
            G_copy, active_sim.target_id, post_impacted, post_alts,
            active_sim.failure_type, active_sim.target_type,
        )

        options.append(RecoveryOption(
            recovery_target_id=cid,
            recovery_type="component",
            services_recovered=recovered,
            services_recovered_count=len(recovered),
            services_still_affected=still_affected,
            services_still_affected_count=len(still_affected),
            projected_impact_score=projected_score,
            no_additional_recovery=(len(recovered) == 0),
        ))

    return options


def _edge_recovery(
    G: nx.DiGraph,
    active_sim: ActiveSimulation,
    original_impacted: dict[str, int],
) -> Optional[RecoveryOption]:
    G_copy = G.copy()
    edge_source: Optional[str] = None
    edge_target: Optional[str] = None

    for u, v, data in G_copy.edges(data=True):
        if data.get("edge_id") == active_sim.target_id:
            G_copy[u][v]["is_present"] = True
            edge_source, edge_target = u, v
            break

    if edge_source is None:
        return None

    post_impacted, post_alts = find_impacted_components(
        G_copy, failed_node=edge_source,
        failed_node_ids=set(), failed_edge_ids=set(),
    )

    recovered = list(set(original_impacted.keys()) - set(post_impacted.keys()))
    still_affected = list(post_impacted.keys())

    projected_score, _ = compute_impact_score(
        G_copy, edge_source, post_impacted, post_alts,
        active_sim.failure_type, "edge",
        failed_edge_source=edge_source, failed_edge_target=edge_target,
    )

    return RecoveryOption(
        recovery_target_id=active_sim.target_id,
        recovery_type="edge",
        services_recovered=recovered,
        services_recovered_count=len(recovered),
        services_still_affected=still_affected,
        services_still_affected_count=len(still_affected),
        projected_impact_score=projected_score,
        no_additional_recovery=(len(recovered) == 0),
    )
