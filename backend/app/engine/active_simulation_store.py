"""
In-memory Active Simulation Store for ImpactLens.

Stores one ActiveSimulation per scenario_id in process memory.
This state is intentionally ephemeral:
- It is NOT written to the database.
- It is lost when the API server restarts.
- The frontend detects absence via GET /scenarios/{id}/simulation returning HTTP 204.

Thread safety: a threading.Lock guards all dict operations. This handles the case
where FastAPI's async event loop offloads blocking DB calls to a thread pool.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ActiveSimulation:
    """
    Represents a single in-flight failure experiment on a scenario's baseline graph.

    Fields:
        scenario_id   : The scenario this simulation is applied to.
        sim_id        : UUID matching the simulation_history record in the DB.
        target_type   : "component" or "edge".
        target_id     : UUID of the failed Component or Edge.
        failure_type  : One of component_unavailable, component_degraded,
                        dependency_link_unavailable.
        impact_report : The full ImpactReport dict cached from when the simulation ran.
        created_at    : UTC timestamp of when the simulation was created.
    """
    scenario_id: str
    sim_id: str
    target_type: str
    target_id: str
    failure_type: str
    impact_report: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ActiveSimulationStore:
    """
    Thread-safe in-memory store for ActiveSimulation objects, keyed by scenario_id.

    At most one ActiveSimulation per scenario at any time.
    All state is lost on server restart — this is by design.
    """

    def __init__(self) -> None:
        self._store: dict[str, ActiveSimulation] = {}
        self._lock = threading.Lock()

    def set(self, scenario_id: str, sim: ActiveSimulation) -> None:
        """Store or replace the ActiveSimulation for a scenario."""
        with self._lock:
            self._store[scenario_id] = sim

    def get(self, scenario_id: str) -> Optional[ActiveSimulation]:
        """Return the ActiveSimulation for a scenario, or None if absent."""
        with self._lock:
            return self._store.get(scenario_id)

    def clear(self, scenario_id: str) -> None:
        """Remove the ActiveSimulation for a scenario (reset simulation)."""
        with self._lock:
            self._store.pop(scenario_id, None)

    def has(self, scenario_id: str) -> bool:
        """Return True if an ActiveSimulation exists for this scenario."""
        with self._lock:
            return scenario_id in self._store


# Module-level singleton used by all routers
active_sim_store = ActiveSimulationStore()
