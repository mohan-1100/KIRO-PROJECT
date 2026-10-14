# Implementation Plan: ImpactLens — Explainable Network Dependency and Outage Impact Simulator

## Overview

ImpactLens is a web-based simulation tool that visualises infrastructure dependency graphs,
models component failures, identifies all affected services via BFS graph traversal, and
explains *why* each service is affected through traceable dependency chains.

The implementation follows the architecture in `design.md`: a FastAPI/Python backend with
NetworkX graph traversal and a SQLite database, paired with a React/Vite/TypeScript frontend
using React Flow for the interactive canvas. All computation is deterministic and runs on
Windows without Docker, AWS credentials, or paid external APIs.

---

## Tasks

---

### Group 1: Project Scaffolding

- [x] 1. Create backend Python/FastAPI project structure
  - Create `backend/` directory with the full `app/` package layout from design.md:
    `app/main.py`, `app/routers/`, `app/models/`, `app/db/`, `app/db/crud/`,
    `app/engine/`, `app/seed/`, `app/seed/fixtures/`
  - Create empty `__init__.py` in every package directory
  - Create `backend/requirements.txt` with pinned versions from design.md:
    `fastapi==0.115.0`, `uvicorn[standard]==0.30.6`, `pydantic==2.8.2`,
    `networkx==3.3`, `hypothesis==6.112.0`, `pytest==8.3.2`,
    `pytest-anyio==0.0.0`, `httpx==0.27.0`
  - Create `backend/.env` with `DATABASE_URL=sqlite:///./impactlens.db` and
    `CORS_ORIGIN=http://localhost:5173`
  - Create `backend/tests/` directory with empty `conftest.py` and `__init__.py`
  - Acceptance: `python -m pytest backend/tests/ -v` exits 0 (no tests yet, no errors)
  - _Requirements: 9, 10_

  - [x] 1.1 Scaffold backend directory structure and requirements.txt
    - Create all directories and `__init__.py` files
    - Write `requirements.txt` with all pinned dependencies listed above
    - Write `backend/.env` with DATABASE_URL and CORS_ORIGIN defaults
    - _Requirements: 9.10, 10.1_

  - [ ]* 1.2 Verify backend scaffolding installs cleanly
    - On Windows: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
    - Assert exit code 0; assert `import fastapi`, `import networkx`, `import hypothesis` all succeed
    - _Requirements: 9_

- [x] 2. Create frontend React/Vite/TypeScript/Tailwind project structure
  - Scaffold with `npm create vite@latest frontend -- --template react-ts`
  - Install additional packages: `react-router-dom`, `@xyflow/react`, `lucide-react`,
    `recharts`, `tailwindcss`, `postcss`, `autoprefixer`
  - Configure Tailwind: run `npx tailwindcss init -p`, set content paths to `./src/**/*.{ts,tsx}`
  - Create `frontend/src/api/`, `frontend/src/contexts/`, `frontend/src/pages/`,
    `frontend/src/components/` directories
  - Create `frontend/src/__tests__/` directory
  - Create `frontend/.env` with `VITE_API_URL=http://localhost:8000`
  - Acceptance: `npm run build` inside `frontend/` exits 0 with no TypeScript errors
  - _Requirements: 11_

  - [x] 2.1 Scaffold frontend project with Vite and install all dependencies
    - Run Vite scaffold, install all listed npm packages
    - Configure Tailwind with dark-palette defaults (`bg-slate-950`, `bg-slate-900` etc.)
    - _Requirements: 11.1_

  - [ ]* 2.2 Verify frontend build passes with zero TypeScript errors
    - Run `npm run build` and assert exit 0
    - _Requirements: 11_

- [x] 3. Create workspace README with Windows setup instructions
  - Write `README.md` at workspace root covering:
    - Prerequisites (Python 3.11+, Node 20+)
    - Backend setup: `python -m venv .venv`, activate, `pip install -r requirements.txt`,
      `uvicorn app.main:app --reload --port 8000`
    - Frontend setup: `npm install`, `npm run dev`
    - Environment variables explanation (DATABASE_URL, CORS_ORIGIN, VITE_API_URL)
    - Verification: visit http://localhost:5173 and http://localhost:8000/docs
    - DB reset procedure: delete `backend/impactlens.db` and restart API
    - How to run backend tests: `pytest backend/tests/ -v`
    - How to run frontend tests: `npx vitest --run`
    - Known limitations (no multi-step recovery, no real AWS, no auth, no Docker)
  - _Requirements: All_

---

### Group 2: Database Layer

- [x] 4. Implement DB connection module and schema creation
  - [x] 4.1 Write `app/db/connection.py` with `get_db_connection()`
    - Returns a `sqlite3.Connection` with `PRAGMA foreign_keys = ON;` enabled on every connection
    - Uses `DATABASE_URL` env var (strips `sqlite:///` prefix to get file path)
    - _Requirements: 10.1, 10.2_

  - [x] 4.2 Write `app/db/schema.py` with `create_tables()`
    - Implement all five `CREATE TABLE IF NOT EXISTS` statements:
      `scenarios`, `components`, `edges`, `simulation_history`, `settings`
    - Include all indexes: `idx_components_scenario`, `idx_edges_scenario`,
      `idx_edges_source`, `idx_edges_target`, `idx_simhist_scenario`, `idx_simhist_status`
    - Insert default settings row: `('freshness_threshold_hours', '72')` using `INSERT OR IGNORE`
    - `components.data_quality_score` has `CHECK(data_quality_score BETWEEN 0 AND 100)`
    - `simulation_history.impact_score` and `data_confidence_score` have matching CHECK constraints
    - `edges` has `UNIQUE(scenario_id, source_component_id, target_component_id)`
    - _Requirements: 10.2, 10.5_

  - [ ]* 4.3 Write unit tests for DB schema creation
    - In `backend/tests/conftest.py` create an in-memory SQLite fixture: call `create_tables()` on `':memory:'`
    - Assert all 5 tables exist via `SELECT name FROM sqlite_master WHERE type='table'`
    - Assert `PRAGMA foreign_key_list(edges)` returns refs to `scenarios` and `components`
    - Assert inserting a component with `data_quality_score=101` raises `IntegrityError`
    - _Requirements: 10.2, 10.5_

- [x] 5. Implement CRUD helpers for all tables
  - [x] 5.1 Write `app/db/crud/scenarios.py`
    - `create_scenario(db, name, description) -> dict` — inserts, returns full row
    - `get_scenario(db, scenario_id) -> dict | None`
    - `list_scenarios(db) -> list[dict]` — ordered by `created_at` ASC
    - `delete_scenario(db, scenario_id) -> bool` — CASCADE deletes components/edges/history
    - _Requirements: 9.13_

  - [x] 5.2 Write `app/db/crud/components.py`
    - `create_component(db, scenario_id, **fields) -> dict`
    - `get_component(db, scenario_id, component_id) -> dict | None`
    - `list_components(db, scenario_id) -> list[dict]`
    - `update_component(db, scenario_id, component_id, **fields) -> dict | None`
    - `delete_component(db, scenario_id, component_id) -> bool`
    - Enforce case-insensitive unique name check at application layer (not DB constraint)
    - _Requirements: 2.1–2.7, 9.1_

  - [x] 5.3 Write `app/db/crud/edges.py`
    - `create_edge(db, scenario_id, source_id, target_id, **fields) -> dict`
    - `get_edge(db, scenario_id, edge_id) -> dict | None`
    - `list_edges(db, scenario_id) -> list[dict]`
    - `update_edge(db, scenario_id, edge_id, label, evidence_source) -> dict | None`
      (source and target are immutable — only label and evidence_source are updatable)
    - `delete_edge(db, scenario_id, edge_id) -> bool`
    - _Requirements: 2.8–2.13, 9.2_

  - [x] 5.4 Write `app/db/crud/simulation_history.py`
    - `create_simulation_history(db, scenario_id, **fields) -> dict`
    - `get_simulation_history(db, history_id) -> dict | None`
    - `list_simulation_history(db, scenario_id) -> list[dict]` — reverse-chronological
    - `list_all_incidents(db) -> list[dict]` — all scenarios, reverse-chronological
    - `update_incident_status(db, incident_id, status) -> dict | None`
    - _Requirements: 3.7, 9.5, 9.14, 15.3_

  - [x] 5.5 Write `app/db/crud/settings.py`
    - `get_setting(db, key) -> str | None`
    - `set_setting(db, key, value) -> None`
    - Convenience: `get_freshness_threshold(db) -> int` and `set_freshness_threshold(db, hours: int)`
    - _Requirements: 7.4, 9.8, 16.1_

  - [ ]* 5.6 Write unit tests for CRUD helpers
    - In `backend/tests/` create `test_crud.py` using the in-memory DB fixture
    - Test `create_scenario` → `get_scenario` round-trip
    - Test duplicate component name (same scenario, different case) is rejected at app layer
    - Test `delete_component` with an edge present returns the edge IDs in the error
    - Test `create_edge` with `source_id == target_id` is rejected (self-loop)
    - Test cascade: `delete_scenario` removes all child components and edges
    - _Requirements: 2.2, 2.3, 2.6, 2.7, 2.8, 10.2_

---

### Group 3: Scenario and Graph API

- [x] 6. Implement Pydantic models and RFC 7807 error handling
  - [x] 6.1 Write `app/models/common.py`
    - `ProblemDetail` Pydantic model with fields: `type`, `title`, `status`, `detail`, `instance`
    - Shared enums: `ComponentType`, `Criticality`, `HealthStatus`, `EvidenceSource`, `ConfirmationStatus`
    - `CRITICALITY_WEIGHTS` dict: `{"low": 1, "medium": 2, "high": 3, "critical": 4}`
    - _Requirements: 9.9_

  - [x] 6.2 Write `app/models/scenario.py`, `component.py`, `edge.py`
    - `ScenarioCreate`, `ScenarioResponse`
    - `ComponentCreate`, `ComponentUpdate`, `ComponentResponse`
    - `EdgeCreate`, `EdgeUpdate`, `EdgeResponse`
    - All required fields validated; optional fields with defaults
    - `data_quality_score` validated to range 0–100 with clear error message
    - `evidence_source` and `confirmation_status` validated against enums
    - _Requirements: 2.2, 7.9, 7.10_

  - [x] 6.3 Configure FastAPI app in `app/main.py`
    - Create `FastAPI(lifespan=lifespan, title="ImpactLens API", version="1.0.0")`
    - `lifespan` calls `create_tables()` then `run_seed_if_needed()` on startup
    - Register global `HTTPException` handler returning `ProblemDetail` JSON
    - Configure CORS: `allow_origins=[CORS_ORIGIN]`, `allow_methods=["*"]`, `allow_headers=["*"]`
    - Include all routers (stubs for now; filled in later tasks)
    - _Requirements: 9.9, 9.10, 9.11, 9.15_

  - [ ]* 6.4 Test RFC 7807 error format
    - Using `httpx.AsyncClient` with the FastAPI test app, trigger a 404 and a 422
    - Assert response body has keys: `type`, `title`, `status`, `detail`, `instance`
    - Assert `Content-Type` is `application/json`
    - _Requirements: 9.9_

- [x] 7. Implement Scenario and Graph endpoints
  - [x] 7.1 Write `app/routers/scenarios.py`
    - `GET /scenarios` → `list_scenarios()`, returns array ordered by `created_at` ASC
    - `POST /scenarios` → validates name present, checks duplicate, calls `create_scenario()`
    - `DELETE /scenarios/{scenario_id}` → `delete_scenario()` with cascade; 404 if missing
    - _Requirements: 9.13_

  - [x] 7.2 Write graph endpoint in `app/routers/scenarios.py`
    - `GET /scenarios/{scenario_id}/graph` → `list_components()` + `list_edges()`,
      returns `{ scenario_id, components: [...], edges: [...] }` within 2 s
    - 404 if scenario not found
    - _Requirements: 9.3_

  - [ ]* 7.3 Write API tests for scenario and graph endpoints
    - `test_api_scenarios.py` using FastAPI `TestClient`
    - Test `POST /scenarios` with valid body → 200, id assigned
    - Test `POST /scenarios` duplicate name → 409 with RFC 7807 body
    - Test `GET /scenarios` returns list ordered by `created_at` ASC
    - Test `DELETE /scenarios/{id}` cascade removes components
    - Test `GET /scenarios/{id}/graph` with no components → `{ components: [], edges: [] }`
    - _Requirements: 9.3, 9.9, 9.13_

- [x] 8. Implement Component and Edge CRUD endpoints
  - [x] 8.1 Write `app/routers/components.py` with all 5 CRUD endpoints
    - `POST /scenarios/{scenario_id}/components` — `ComponentCreate` body; 422 missing
      required field or invalid enum/DQ score; 409 duplicate name (case-insensitive)
    - `GET /scenarios/{scenario_id}/components` — list all
    - `GET /scenarios/{scenario_id}/components/{id}` — single; 404 if missing
    - `PUT /scenarios/{scenario_id}/components/{id}` — full update; 422 on validation
    - `DELETE /scenarios/{scenario_id}/components/{id}` — 409 with `edge_ids` if edges exist
    - All responses include assigned `id`; all operations within 2 s
    - _Requirements: 2.1–2.7, 9.1_

  - [x] 8.2 Write `app/routers/edges.py` with all 5 CRUD endpoints
    - `POST /scenarios/{scenario_id}/edges` — 422 self-loop; 409 duplicate; cross-scenario
      validation: both `source_component_id` and `target_component_id` must belong to `scenario_id`,
      return 422 identifying the offending component ID if not
    - `GET /scenarios/{scenario_id}/edges` — list all
    - `GET /scenarios/{scenario_id}/edges/{id}` — single; 404 if missing
    - `PUT /scenarios/{scenario_id}/edges/{id}` — update `label` and `evidence_source` only;
      `source_component_id` and `target_component_id` are immutable
    - `DELETE /scenarios/{scenario_id}/edges/{id}` — always succeeds if found; 404 if missing
    - _Requirements: 2.8–2.13, 9.2_

  - [ ]* 8.3 Write API tests for Component and Edge endpoints
    - `test_api_components.py`: test 422 on missing `name`; 409 on duplicate name different case;
      409 on delete with existing edge (assert `edge_ids` in body)
    - `test_api_edges.py`: test 422 on self-loop; 409 on duplicate edge; 200 on valid create;
      test cross-scenario edge rejection (422 with correct detail); test edge update preserves
      `source_component_id` and `target_component_id`
    - _Requirements: 2.1–2.13, 9.1, 9.2_

---

### Group 4: Simulation API

- [x] 9. Implement simulation request/response models
  - Write `app/models/simulation.py`
    - `SimulationRequest`: `scenario_id`, `target_type` (enum: component/edge),
      `target_id`, `failure_type` (enum: component_unavailable/component_degraded/dependency_link_unavailable)
    - `ImpactReport`: full response structure matching the JSON shape in design.md (sim_id,
      scenario_id, failed_target_id, failed_target_type, failure_type, impact_score,
      data_confidence_score, score_breakdown, low_confidence_notice, already_failed_warning,
      directly_affected, transitively_affected, impact_paths, possible_alt_path_components,
      simulated_projection_label, timestamp)
    - Validate target_type + failure_type combinations in the Pydantic validator:
      `component` → only `component_unavailable` or `component_degraded`;
      `edge` → only `dependency_link_unavailable`; else raise `ValueError`
    - Write `app/models/recovery.py`: `RecoveryRequest`, `RecoveryOption`, `RecoveryResponse`
    - _Requirements: 3.1, 3.2, 4.8_

- [x] 10. Implement Active Simulation Store
  - Write `app/engine/active_simulation_store.py` exactly as in design.md
    - `ActiveSimulation` dataclass with fields: `scenario_id`, `sim_id`, `target_type`,
      `target_id`, `failure_type`, `impact_report`, `created_at`
    - `ActiveSimulationStore` class with thread-safe `threading.Lock()` protecting a `dict`
    - Methods: `set(scenario_id, sim)`, `get(scenario_id) -> Optional[ActiveSimulation]`,
      `clear(scenario_id)`
    - Module-level singleton: `active_sim_store = ActiveSimulationStore()`
    - _Requirements: 3, 9_

- [ ] 11. Implement Simulation, Reset, History, Incident, Settings, and Data Quality endpoints
  - [x] 11.1 Write `app/routers/simulations.py`
    - `POST /scenarios/{scenario_id}/simulations` — validate request, check target belongs
      to scenario (404 if not), run simulation via `run_simulation()` (stub for now),
      store in `active_sim_store`, write to `simulation_history`, return `ImpactReport`
    - `GET /scenarios/{scenario_id}/simulations` — return history in reverse-chronological order
    - `GET /scenarios/{scenario_id}/simulation` — return active sim (200) or 204 if none
    - `POST /scenarios/{scenario_id}/reset` — call `active_sim_store.clear()`, return 200;
      must NOT modify any DB record
    - _Requirements: 3.1, 3.4, 3.7, 9.4, 9.5, 9.7, 9.12_

  - [ ] 11.2 Write `app/routers/incidents.py`
    - `GET /incidents` — `list_all_incidents()`, reverse-chronological, all scenarios
    - `PATCH /incidents/{incident_id}` — body `{ "status": "resolved" }`; 422 if status ≠ "resolved";
      404 if not found
    - _Requirements: 9.14_

  - [x] 11.3 Write `app/routers/settings.py`
    - `GET /settings` → `{ "freshness_threshold_hours": <int> }`
    - `PUT /settings` → validate value is integer 1–8760; 422 outside range; persist and return updated
    - _Requirements: 7.4, 9.8, 16.1_

  - [x] 11.4 Write `app/routers/data_quality.py`
    - `GET /scenarios/{scenario_id}/data-quality` — returns `data_completeness_indicator`
      (count confirmed / total × 100, rounded), `freshness_threshold_hours`,
      per-component metadata with `is_stale` and `hours_since_observed` flags,
      per-edge metadata with `is_stale`
    - Staleness = `last_observed_at` age > `freshness_threshold_hours`
    - _Requirements: 7.3, 7.6, 9.8_

  - [ ]* 11.5 Write API tests for simulation and settings endpoints
    - `test_api_simulations.py`:
      - Test `POST .../simulations` with `target_type="component"` and
        `failure_type="dependency_link_unavailable"` → 422 (Req 14 AC 1q)
      - Test `POST .../simulations` with `target_type="edge"` and
        `failure_type="component_unavailable"` → 422 (Req 14 AC 1q)
      - Test `GET .../simulation` when no active sim → 204
      - Test `POST .../reset` does not modify any component's health_status in DB
    - `test_api_settings.py`:
      - Test `PUT /settings` with value 0 → 422
      - Test `PUT /settings` with value 8761 → 422
      - Test `PUT /settings` with value 48 → 200, persisted
    - _Requirements: 3.2, 3.4, 9.7, 9.8, 14.1_

---

### Group 5: Graph and Impact Engine

- [x] 12. Implement `graph_builder.py`
  - Write `app/engine/graph_builder.py` implementing `build_simulation_graph()` exactly
    as specified in design.md
  - Input: `components: list`, `edges: list`, `active_sim: Optional[ActiveSimulation]`
  - Output: `tuple[nx.DiGraph, set[str], set[str]]` (graph, failed_node_ids, failed_edge_ids)
  - Step 1: Add all nodes with attributes (`name`, `criticality_weight`, `health_status`,
    `data_quality_score`) — use `CRITICALITY_WEIGHTS` from `common.py`
  - Step 2: Add all edges with `edge_id` and `is_present=True`
  - Step 3: Apply simulation overlay — three code paths:
    - `component_unavailable`: add node to `failed_node_ids`, set `health_status="failed"`
    - `component_degraded`: set `health_status="degraded"`, do NOT add to `failed_node_ids`
    - `dependency_link_unavailable`: find edge by `edge_id`, set `is_present=False`,
      add to `failed_edge_ids`
  - _Requirements: 3.1, 3.2, 4.5_

  - [x] 12.1 Implement `build_simulation_graph` with all three failure type code paths
    - _Requirements: 3.2, 4.5_

  - [ ]* 12.2 Write unit tests for `build_simulation_graph`
    - Test `component_unavailable`: node in `failed_node_ids`, health_status="failed"
    - Test `component_degraded`: node NOT in `failed_node_ids`, health_status="degraded"
    - Test `dependency_link_unavailable`: edge `is_present=False`, endpoint nodes health unchanged
    - _Requirements: 3.2_

- [x] 13. Implement `impact_engine.py` — BFS traversal and scoring
  - [x] 13.1 Implement `_find_apparent_alternative_sources()`
    - Iterates predecessors of `dependant`; returns list of source IDs that pass all three conditions:
      (a) edge `is_present=True`, (b) source not in `failed_node_ids`, (c) source not in `current_impacted`
    - _Requirements: 4.3_

  - [x] 13.2 Implement `find_impacted_components()`
    - BFS from `failed_node`; respects `is_present=False` edges (skip) and
      `failed_node_ids` (do not propagate through)
    - For each successor: call `_find_apparent_alternative_sources()`; if non-empty,
      record in `possible_alts` but **still include in `affected`** (conservative design)
    - Returns `(affected: dict[str, int], possible_alts: dict[str, list[str]])`
    - Cycle safety: visited set; each node processed at most once
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.10_

  - [x] 13.3 Implement `compute_impact_score()`
    - Four-factor formula from design.md/Req 4 AC 7:
      `criticality_score = crit_weight / 4`
      `reach_score = min(affected_count, 20) / 20`
      `proximity_score = 1 / (1 + avg_hop_distance)` (0.0 if no dependants)
      `isolation_score = 1 − alt_path_ratio`
    - Weighted sum: 0.35 / 0.30 / 0.20 / 0.15
    - `impact_score = min(100, round(raw_score × 100))`
    - Edge failure: `criticality_score = max(crit_weight(source), crit_weight(target)) / 4`
    - Returns `(impact_score: int, breakdown: dict)` — breakdown labelled
      "ImpactLens heuristic v1.0 — not an industry standard metric"
    - _Requirements: 4.7, 4.14_

  - [x] 13.4 Implement `compute_data_confidence_score()`
    - Arithmetic mean of `data_quality_score` of all involved node IDs, rounded to nearest int
    - Returns 100 if no nodes involved
    - Must NOT affect or modify the Impact Score
    - _Requirements: 4.8, 4.13_

  - [x] 13.5 Implement `build_impact_report()` orchestrator
    - Calls `build_simulation_graph()`, `find_impacted_components()`,
      `compute_impact_score()`, `compute_data_confidence_score()`
    - Sorts affected components in descending order of
      `severity_contribution = criticality_weight × (1 − alt_path_ratio_for_this_component)`;
      ties broken by name ascending
    - Deduplicates: each component appears at most once
    - Sets `low_confidence_notice` when `data_confidence_score < 50`
    - Sets `already_failed_warning` when target's baseline `health_status == "failed"`
    - Checks staleness for all involved components against `freshness_threshold_hours`
    - Returns fully-populated `ImpactReport`
    - _Requirements: 4.2, 4.8, 4.9, 4.10, 4.11, 3.8, 7.3_

  - [x]* 13.6 Write unit tests for impact engine — all 19 Pytest scenarios (Req 14 AC 1)
    - `test_impact_engine.py` using standard test graph `A→B→C, A→D, B→D` from design.md
    - a. `test_direct_dependant_identified` — fail A; B and D at hop 1
    - b. `test_indirect_dependant_identified` — fail A; C at hop 2
    - c. `test_unaffected_component_excluded` — separate node X; not in impacted
    - d. `test_alternative_path_excludes_component` — fail B; D has alt via A; D in `possible_alts`
       but still in `affected`
    - e. `test_cycle_does_not_infinite_loop` — graph with cycle A→B→C→A; terminates
    - f. `test_failed_edge_excluded_from_traversal` — edge A→B failed; B and C not affected
    - g. `test_unknown_status_propagates_uncertainty` — component with `health_status="unknown"`
       included in affected; explanation reflects uncertainty
    - h. `test_stale_evidence_triggers_staleness_warning` — `last_observed_at` > threshold;
       staleness warning in report
    - i. `test_higher_criticality_yields_higher_score` — critical node with 5 dependants scores
       higher than low node with 1 dependant
    - j. `test_two_hop_explanation_matches_template` — known A→B→C graph; explanation text
       matches indirect template exactly
    - k. `test_recovery_highest_downstream_recovers_more` — two candidates; higher-downstream
       candidate recovers more services
    - l. `test_missing_required_field_returns_422` — API endpoint; missing `name` → 422
    - m. `test_reset_clears_active_simulation` — POST reset; GET simulation → 204
    - n. `test_multi_path_component_appears_once` — D reachable via A→D and A→B→D;
       D appears exactly once in affected
    - o. `test_failed_edge_traversal_semantics` — edge A→B failed; B only reachable via A→B
       IS in affected; C (also connects to D via another route) NOT in affected
    - p. `test_impact_score_unchanged_by_dq_scores` — same graph, DQ=0 vs DQ=100;
       impact_score identical in both runs; data_confidence_score differs
    - q. `test_invalid_failure_type_combination_returns_422` — two requests; both → 422
    - r. `test_save_as_scenario_copies_baseline_only` — new scenario has same components/edges;
       health statuses are baseline values, not simulation values
    - s. `test_edge_failure_recovery_offers_one_option` — edge simulation; recovery offers
       exactly one option (restore the edge)
    - Additional tests from design.md review section:
    - `test_component_unavailable_blocks_traversal` — A fails unavailable; B, C in affected
    - `test_component_degraded_traversal_continues` — A fails degraded; B, C still in affected
    - `test_dependency_link_unavailable_blocks_edge` — edge A→B failed; B, C not in affected
    - `test_alternative_path_component_still_in_affected` — D has two predecessors; D in affected
    - `test_no_alternative_path_when_all_sources_impacted` — all predecessors impacted; D not in possible_alts
    - `test_alt_path_ratio_nonzero_when_alternatives_exist` — alt_path_ratio > 0; isolation_score < 1
    - `test_alt_path_ratio_zero_when_no_alternatives` — linear chain; alt_path_ratio = 0; isolation_score = 1
    - `test_data_confidence_score_independence` — assert impact_score identical across DQ values
    - _Requirements: 4.1–4.14, 14.1_

  - [ ]* 13.7 Write property-based tests using Hypothesis (Req 14 AC 3)
    - `test_impact_engine_pbt.py`
    - Property 1 (DAG equivalence): generate random DAGs; for any failed node, `impacted.keys()` ==
      `nx.descendants(G, failed_node)` — max_examples=200 (Req 14 AC 3a)
    - Property 2 (failed-edge subset): for any graph and failed node, removing any edge produces
      impacted set that is a subset of the original — max_examples=200 (Req 14 AC 3b)
    - Property 3 (alternative-path detection reporting): adding a bypass path adds the dependant
      to `possible_alts`; `alt_path_ratio` does not decrease — max_examples=200 (Req 14 AC 3c)
    - _Requirements: 14.3_

- [x] 14. Implement Explanation Engine
  - Write `app/engine/explanation_engine.py` with:
    - `TEMPLATES` dict keyed by `(impact_type, has_alternative, has_dq_warning)` — 8 entries
      covering all combinations of `direct`/`indirect` × has_alternative × has_dq_warning
    - `FAILURE_DESCRIPTIONS` dict mapping failure_type to human-readable string
    - `render_path(path_steps) -> str` — joins component names with " → "
    - `DQ_WARNING_TEMPLATE` string with `{component_name}` and `{score}` placeholders
    - `build_explanation(...)` — selects template, fills variables, returns string
    - Must NOT use any LLM or external AI — pure template substitution
    - Completing within 500 ms is a given since it's synchronous Python string formatting
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

  - [x] 14.1 Implement full template registry and `build_explanation()`
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

  - [ ]* 14.2 Write unit tests for explanation engine
    - Test direct+no-alt+no-dq template fills correctly
    - Test indirect+has-alt+has-dq template fills correctly
    - Test `render_path` with three-step path
    - Test DQ warning fires only when `data_quality_score < 50`
    - _Requirements: 5.2, 5.5_

---

### Group 6: Recovery Engine

- [x] 15. Implement Recovery Engine
  - [x] 15.1 Implement `compute_recovery_options()` for component-failure simulations
    - Enumerate all components with `health_status in ("failed", "degraded")` plus
      the simulation target as recovery candidates
    - For each candidate: clone `G.copy()`, restore node to `health_status="healthy"`,
      re-run `find_impacted_components()`, compute `services_recovered` and `services_still_affected`,
      compute `projected_impact_score` via `compute_impact_score()`
    - Rank options descending by `services_recovered_count`
    - Active simulation state (`active_sim_store`) must NOT be mutated
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 15.2 Implement `compute_recovery_options()` for edge-failure simulations
    - One candidate: restore the failed edge
    - Clone `G.copy()`, find edge by `edge_id`, set `is_present=True`
    - Re-run BFS from `edge_source` on restored graph with empty `failed_node_ids` and `failed_edge_ids`
    - `services_recovered = set(original_impacted.keys()) - set(post_recovery_impacted.keys())`
    - `services_still_affected = set(post_recovery_impacted.keys())`
    - Neither original `G` nor `active_sim_store` is modified
    - _Requirements: 6.1, 6.2, 14.1s_

  - [x] 15.3 Wire recovery engine into `app/routers/simulations.py`
    - `POST /scenarios/{scenario_id}/simulations/{sim_id}/recovery`
    - Body: `{ "recovery_type": "component|edge", "recovery_target_id": "uuid" }`
    - 400 if `recovery_type == "component"` and target not in failed/degraded state
    - 404 if `sim_id` or `recovery_target_id` not found
    - Response includes `simulated_projection_label: "Simulated Projection"` and
      disclosure notice
    - Does NOT alter active simulation state
    - _Requirements: 6.2, 6.6, 6.8, 6.9, 6.10, 9.6_

  - [ ]* 15.4 Write unit tests for recovery engine
    - `test_recovery_engine.py`
    - `test_edge_recovery_delta_is_subset_of_original` — post_recovery ⊆ original
    - `test_edge_recovery_services_recovered_correct` — A→B→C, edge A→B failed;
      after restore, services_recovered = {B, C}
    - `test_edge_recovery_partial_recovery` — partial graph recovery
    - `test_recovery_does_not_mutate_active_simulation` — fetch sim before, call recovery,
      fetch sim after; assert unchanged
    - `test_recovery_does_not_mutate_baseline_graph` — original G edges all `is_present=True`
      after calling `compute_recovery_options()`
    - `test_edge_simulation_cross_scenario_rejected` — attempt simulation with target from
      wrong scenario → 404
    - _Requirements: 6.2, 6.3, 14.1_

---

### Group 7: Seed Data and Demo Scenarios

- [x] 16. Create seed data JSON fixtures
  - [x] 16.1 Write `app/seed/fixtures/scenarios.json`
    - Four scenario objects with fixed deterministic UUIDs and names:
      "Database Failure", "Shared Dependency Failure",
      "Alternative Path Available", "Incomplete Evidence"
    - Each has `id`, `name`, `description`, `created_at` (staggered timestamps for ordering)
    - _Requirements: 8.2_

  - [x] 16.2 Write `app/seed/fixtures/components.json`
    - 14 component objects from design.md seed data table (ShoppingApp through InventoryService)
    - All have `evidence_source="simulated_demo"` and `confirmation_status="inferred"` (Req 7 AC 8)
    - ReportingService has `data_quality_score=20` and `last_observed_at` set to 120 hours
      before a reference timestamp (stale under 72h threshold)
    - Each component is replicated across all 4 scenarios with distinct UUIDs per scenario
    - _Requirements: 8.1, 8.2, 7.8_

  - [x] 16.3 Write `app/seed/fixtures/edges.json`
    - 16 directed edges per scenario (from design.md edge list):
      APIGateway→ShoppingApp, OrderService→ShoppingApp, PaymentService→ShoppingApp,
      UserService→ShoppingApp, AuthService→OrderService, AuthService→PaymentService,
      AuthService→UserService, OrderDB→OrderService, PaymentDB→PaymentService,
      UserDB→UserService, SessionCache→AuthService, NotificationQueue→OrderService,
      PaymentProviderAPI→PaymentService, UserDB→InventoryService, OrderDB→InventoryService,
      OrderDB→ReportingService
    - All have `evidence_source="simulated_demo"` and `confirmation_status="inferred"`
    - _Requirements: 8.1, 8.2_

- [x] 17. Implement `seed_loader.py` and verify demo scenarios
  - [x] 17.1 Write `app/seed/seed_loader.py`
    - `run_seed_if_needed()`: check `SELECT COUNT(*) FROM components`; return immediately if > 0
    - Load JSON fixtures and INSERT all scenarios, components, and edges
    - Idempotent: safe to call on every server startup (Req 8 AC 3)
    - _Requirements: 8.1, 8.2, 8.3, 9.11_

  - [x]* 17.2 Write seed loader tests
    - `test_seed_loader.py`
    - Test `run_seed_if_needed()` on empty DB inserts exactly 4 scenarios and 56 components
      (14 per scenario × 4)
    - Test calling `run_seed_if_needed()` twice does not duplicate any record
    - Test all 4 scenario names are present in the scenarios table
    - Test at least 6 distinct `type` values present in components
    - Test ReportingService has `data_quality_score=20`
    - Test at least one component has `last_observed_at` > 72 hours old (stale under default threshold)
    - _Requirements: 8.1, 8.2, 8.3_

  - [x]* 17.3 Verify four demo scenarios produce deterministic impact results
    - `test_demo_scenarios.py`: for each of the 4 demo scenarios, call
      `POST /scenarios/{id}/simulations` with the expected target
    - "Database Failure": fail OrderDB → assert OrderService and ReportingService in directly_affected;
      InventoryService in `possible_alt_path_components` (has alt via UserDB)
    - "Shared Dependency Failure": fail AuthService → assert OrderService, PaymentService,
      UserService all in directly_affected; ShoppingApp in transitively_affected
    - "Alternative Path Available": fail UserDB → InventoryService in `possible_alt_path_components`;
      UserService in directly_affected
    - "Incomplete Evidence": fail OrderDB → ReportingService has DQ warning in explanation text;
      data_confidence_score < 72 (dragged down by ReportingService DQ=20)
    - Running same test twice produces identical impact_score and affected set
    - _Requirements: 8.2, 4.4, 7.5_

- [x] 18. Checkpoint — backend core complete
  - Run `pytest backend/tests/ -v` — all backend tests pass
  - Start API server: `uvicorn app.main:app --reload --port 8000`
  - Verify http://localhost:8000/docs loads OpenAPI UI
  - Verify `GET /scenarios` returns 4 seeded scenarios
  - Verify `GET /scenarios/{first_id}/graph` returns 14 components and 16 edges
  - _Requirements: 9, 10_

---

### Group 8: Frontend Scaffolding and Layout

- [x] 19. Implement API client layer and shared TypeScript types
  - [x] 19.1 Write `src/api/client.ts`
    - `apiRequest<T>(path, options)` with `BASE_URL` from `import.meta.env.VITE_API_URL`
    - Throws `ApiError(status, body)` on non-ok responses
    - Returns `null as T` for 204 responses
    - _Requirements: 11_

  - [x] 19.2 Write typed API modules
    - `src/api/scenarios.ts`: `listScenarios()`, `createScenario()`, `deleteScenario()`
    - `src/api/graph.ts`: `getGraph(scenarioId)`
    - `src/api/components.ts`: full CRUD
    - `src/api/edges.ts`: full CRUD
    - `src/api/simulations.ts`: `runSimulation()`, `getActiveSimulation()`,
      `resetSimulation()`, `getSimulationHistory()`
    - `src/api/recovery.ts`: `requestRecovery()`
    - `src/api/incidents.ts`: `listIncidents()`, `resolveIncident()`
    - `src/api/settings.ts`: `getSettings()`, `updateSettings()`
    - `src/api/dataQuality.ts`: `getDataQuality()`
    - _Requirements: 9, 11_

  - [x] 19.3 Write shared TypeScript interfaces in `src/types/`
    - `Scenario`, `Component`, `Edge`, `Graph`, `ImpactReport`, `RecoveryOption`,
      `SimulationHistory`, `Incident`, `Settings`, `DataQuality`
    - All fields typed; enums as TypeScript union types or `enum`
    - _Requirements: 11_

- [x] 20. Implement React Context providers
  - [x] 20.1 Write `src/contexts/ScenarioContext.tsx`
    - `ScenarioContextValue` with `scenarios`, `activeScenarioId`, `setActiveScenarioId`,
      `activeScenario`
    - Loads scenarios on mount from `GET /scenarios`
    - Auto-selects first scenario on first load (ordered by `created_at` ASC)
    - _Requirements: 8.4, 8.5, 11.2_

  - [x] 20.2 Write `src/contexts/SimulationContext.tsx`
    - `SimulationContextValue` with `simulationOverlay`, `setSimulationOverlay`, `clearOverlay()`
    - `SimulationOverlay` interface: `simId`, `failedTargetId`, `failedTargetType`,
      `failureType`, `affectedComponentIds`, `alternativePathComponentIds`, `impactReport`
    - When scenario changes: `clearOverlay()` without sending reset to API
    - _Requirements: 3.3, 3.4, 8.5_

- [x] 21. Implement App layout shell
  - [x] 21.1 Write `src/components/layout/TopBar.tsx`
    - Brand name "ImpactLens" at left
    - `ScenarioPicker` dropdown: list all scenarios, selected = `activeScenarioId`;
      on selection change: `clearOverlay()`, `setActiveScenarioId()`, fetch new scenario's graph
      and active simulation (Req 8 AC 5)
    - `EnvironmentBadge` always showing "Simulated Demo"
    - `SimulationActiveIndicator`: hidden when no overlay; shows component name + failure type
      for component simulations; shows source → target + "dependency link unavailable" for edge
      simulations (Req 3 AC 3)
    - _Requirements: 3.3, 8.4, 11.2_

  - [x] 21.2 Write `src/components/layout/Sidebar.tsx`
    - Collapsible left sidebar (toggle button)
    - 8 `NavLink` entries: Overview, Dependency Map, Failure Simulator,
      Incident Analysis, Recovery Planner, Infrastructure Inventory,
      Simulation History, Settings & Data Quality
    - Active route highlighted
    - _Requirements: 11.1_

  - [x] 21.3 Write `src/components/layout/DetailsPanel.tsx`
    - Right-side sliding panel (`w-96`), opens when `selectedComponent` is set
    - Close button and click-outside dismiss
    - Three tabs: Overview, Impact Paths, Data Quality
    - Overview tab: type badge, health status badge (icon + label, NOT color-only), criticality,
      evidence source, confirmation status, last observed with staleness indicator, DQ score bar
    - Impact Paths tab: visible only when simulation active; `ImpactPathEntry × n`;
      collapsed by default if > 3 paths, expanded if ≤ 3 (Req 5 AC 6)
    - Data Quality tab: DQ score gauge, evidence source, uncertainty notice if `confirmation_status="unknown"`
    - _Requirements: 1.3, 5.6, 11.3_

  - [x] 21.4 Wire `App.tsx` with React Router, contexts, and layout
    - Wrap with `ScenarioProvider` and `SimulationProvider`
    - `<Layout>` containing `<TopBar>`, `<Sidebar>`, `<Outlet>`, `<DetailsPanel>`
    - 8 routes mapped to page components (stubs for now)
    - Full 1280px+ width, no horizontal scroll (Req 11 AC 4)
    - No login screen (Req 11 AC 5)
    - _Requirements: 11.1, 11.4, 11.5_

---

### Group 9: Dependency Map Page

- [ ] 22. Implement custom React Flow node types
  - [~] 22.1 Write `src/components/graph/CustomNode.tsx`
    - One node component per `ComponentType` — use Lucide icons as specified in design.md:
      `Globe`(web_app), `Zap`(api), `Database`(database), `Layers`(cache),
      `Shield`(auth), `MessageSquare`(queue), `CreditCard`(payment),
      `ExternalLink`(external_api), `GitMerge`(load_balancer)
    - Health status badge: text label + icon (`CheckCircle`/`AlertTriangle`/`XCircle`/`HelpCircle`);
      NEVER communicated by color alone (Req 1 AC 5)
    - Criticality pill
    - If `confirmation_status="unknown"`: dashed border + `?` badge (Req 7 AC 7)
    - Simulation overlay styles when `simulationOverlay` is active:
      failed target → red ring + XCircle; affected → amber ring + warning;
      possible-alt → blue-dashed ring + info; unaffected → default
    - _Requirements: 1.2, 1.4, 1.5, 1.6, 3.3, 7.7_

  - [~] 22.2 Write `src/components/graph/CustomEdge.tsx`
    - Directed arrows using React Flow edge with `markerEnd: { type: MarkerType.ArrowClosed }`
    - Renders edge label when present
    - _Requirements: 1.2_

- [ ] 23. Implement Dependency Map page
  - [x] 23.1 Write `src/pages/DependencyMapPage.tsx`
    - Fetch `GET /scenarios/{scenarioId}/graph` on scenario change
    - Render `ReactFlow` canvas with `pan`, `zoom` controls (10%–200%, Req 1 AC 1)
    - Register all 9 custom node types and custom edge type
    - On node click: set `selectedComponent` to open `DetailsPanel`
    - Load error state: error indicator in canvas + retry control (Req 1 AC 12)
    - "No matching components" message when filters exclude all nodes (Req 1 AC 11)
    - _Requirements: 1.1, 1.2, 1.3, 1.12_

  - [~] 23.2 Write `src/components/graph/FilterToolbar.tsx`
    - Dropdowns for Component type, health status, criticality level
    - Filter applied client-side on already-loaded graph data — no API call on filter change
    - Filtered results within 500ms (client-side, guaranteed by avoiding network)
    - _Requirements: 1.7, 1.8, 1.9_

  - [~] 23.3 Write `src/components/graph/SearchBar.tsx`
    - Text input accepting 1–200 characters
    - Case-insensitive substring match on component names
    - Highlights matching nodes and scrolls to bring at least one into view within 500ms
    - _Requirements: 1.10, 1.11_

  - [~] 23.4 Implement impact path highlight on explanation click
    - When user clicks an `ImpactPathEntry` in `DetailsPanel`:
      highlight all nodes and edges in that path on the canvas within 300ms
    - Deselect restores previous visual state
    - _Requirements: 5.7_

---

### Group 10: Overview Dashboard

- [ ] 24. Implement Overview page
  - [x] 24.1 Write `src/pages/OverviewPage.tsx`
    - Fetch all 6 summary metrics from API (no hardcoded values, Req 12 AC 2):
      total components, healthy count, degraded count, failed count,
      active incident count (status="open"), potentially affected services count
      (from active simulation impacted set, 0 if none)
    - Metrics derived from: `GET /scenarios/{id}/graph` (component counts),
      `GET /incidents` filtered for open status, `GET /scenarios/{id}/simulation`
    - Each metric card shows label + value
    - _Requirements: 12.1, 12.2_

  - [~] 24.2 Implement non-interactive graph miniature preview
    - Render a small read-only React Flow canvas (minimap-style) on the Overview page
    - No pan/zoom controls; no node click handler
    - _Requirements: 12.3_

  - [~] 24.3 Implement recent simulations list and most critical components
    - Recent simulations: 3 most recent from `GET /scenarios/{id}/simulations`;
      show failed component name, failure type, timestamp
    - Most Critical Components: top 5 by criticality weight from active scenario's component list
    - _Requirements: 12.4, 12.5_

  - [~] 24.4 Implement Data Completeness Indicator
    - Fetch `GET /scenarios/{id}/data-quality`; display `data_completeness_indicator` as
      both a numeric percentage and a progress bar
    - _Requirements: 7.6, 12.6_

  - [~] 24.5 Implement API error handling on Overview page
    - When any metric fetch fails: display error notice identifying which metric failed + retry control
    - _Requirements: 12.7_

---

### Group 11: Failure Simulator and Incident Analysis Pages

- [ ] 25. Implement Failure Simulator page
  - [x] 25.1 Write `src/pages/FailureSimulatorPage.tsx`
    - Component selector dropdown (from active scenario's component list)
    - Edge selector dropdown (from active scenario's edge list)
    - `target_type` toggle: "Component" or "Edge"
    - `failure_type` selector: shows `component_unavailable`/`component_degraded` when
      target_type="component"; shows `dependency_link_unavailable` when target_type="edge"
    - "Run Simulation" button: calls `POST /scenarios/{id}/simulations`; on success
      sets `simulationOverlay` in context
    - Displays returned `ImpactReport` summary: impact_score, affected count, score breakdown
      labelled "ImpactLens heuristic v1.0"
    - _Requirements: 3.1, 3.2, 4.7, 4.8_

  - [~] 25.2 Implement Reset Simulation and Save as Scenario actions
    - "Reset Simulation" button: `POST /scenarios/{id}/reset`; on success `clearOverlay()`;
      restores all nodes to baseline without page reload (Req 3 AC 4)
    - "Save Simulation as Scenario" button + name input:
      validates name non-empty before sending (Req 3 AC 6);
      `POST /scenarios` with new name to create independent copy;
      new scenario appears in Scenario Picker immediately (Req 3 AC 12)
    - _Requirements: 3.4, 3.5, 3.6, 3.12_

- [x] 26. Implement Incident Analysis page
  - Write `src/pages/IncidentAnalysisPage.tsx`
  - List all incidents from `GET /incidents` in reverse-chronological order
  - Each row: simulation identifier, failed target name, failure type, timestamp,
    affected service count, impact score, status badge
  - "Mark Resolved" action: `PATCH /incidents/{id}` with `{ status: "resolved" }`
  - Updates status badge in list without full reload
  - _Requirements: 11.1, 9.14_

---

### Group 12: Recovery Planner Page

- [ ] 27. Implement Recovery Planner page
  - [x] 27.1 Write `src/pages/RecoveryPlannerPage.tsx`
    - Show "No active simulation" message when `simulationOverlay` is null (Req 6 AC 11)
    - When simulation active: display list of recovery candidates
    - For component failures: enumerate all failed/degraded components as candidates
    - For edge failures: one candidate "Restore failed edge [source → target]"
    - _Requirements: 6.1, 6.11_

  - [~] 27.2 Implement recovery comparison table
    - Side-by-side table of up to 4 recovery scenarios (Req 6 AC 5)
    - For component failure rows: candidate name, services recovered count,
      services still affected count, projected impact score
    - For edge failure row: edge identifier, same columns
    - Each row triggers `POST .../recovery` when selected for comparison
    - _Requirements: 6.5_

  - [~] 27.3 Implement delta display and disclosure notices
    - Delta: "N services recovered, M services still affected"
    - "No additional services recovered" notice when `services_recovered_count=0` (Req 6 AC 7)
    - "Simulated Projection" label on every recovery result (Req 6 AC 6)
    - Disclosure notice on every result: "Recovery analysis is a simulated projection..."
      (Req 6 AC 9)
    - _Requirements: 6.3, 6.6, 6.7, 6.9_

---

### Group 13: Infrastructure Inventory, Simulation History, and Settings Pages

- [ ] 28. Implement Infrastructure Inventory page
  - [x] 28.1 Write `src/pages/InfrastructureInventoryPage.tsx`
    - Sortable, filterable table: name, type, health status, criticality, evidence source,
      confirmation status, data quality score, last observed (Req 13 AC 1)
    - Row click: navigate to Dependency Map with that component selected and details panel open
      (Req 13 AC 2)
    - _Requirements: 13.1, 13.2_

  - [~] 28.2 Implement inline editing for evidence_source, confirmation_status, data_quality_score
    - Write `src/components/inventory/EditableTableRow.tsx`
    - Inline edit fields for the three editable columns
    - Save sends `PUT /scenarios/{id}/components/{id}`; reflects change without full reload
    - On API error: display error in the row and restore previous value (Req 13 AC 5)
    - _Requirements: 13.3, 13.4, 13.5_

- [x] 29. Implement Simulation History page
  - Write `src/pages/SimulationHistoryPage.tsx`
  - All history records in reverse-chronological order: sim identifier, failed component name,
    failure type, timestamp, affected service count, impact score (Req 15 AC 1)
  - Row click: open `DetailsPanel` with read-only replay of the full impact report (Req 15 AC 2)
  - _Requirements: 15.1, 15.2_

- [ ] 30. Implement Settings & Data Quality page
  - [x] 30.1 Write `src/pages/SettingsDataQualityPage.tsx`
    - Freshness Threshold control: numeric input with 1–8760 validation;
      client-side validation before API call (Req 16 AC 4);
      `PUT /settings` on save; error message if API fails + retain previous value (Req 16 AC 5)
    - Per-component evidence coverage table: name, evidence_source, confirmation_status,
      data_quality_score, last_observed_at; sortable by each column (Req 16 AC 2)
    - _Requirements: 16.1, 16.2, 16.4, 16.5_

  - [~] 30.2 Implement data quality distribution chart
    - Recharts chart showing count of components per `confirmation_status` bucket:
      confirmed, inferred, unknown (Req 16 AC 3)
    - _Requirements: 16.3_

---

### Group 14: Frontend Tests

- [x] 31. Set up Vitest and React Testing Library
  - Install `vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
    `@testing-library/user-event`, `jsdom`
  - Configure `vite.config.ts` with `test: { environment: 'jsdom' }`
  - Write `src/__tests__/setup.ts` importing `@testing-library/jest-dom`
  - Acceptance: `npx vitest --run` exits 0 on empty test suite
  - _Requirements: 14.2_

- [ ] 32. Write 6 required frontend test cases (Req 14 AC 2)
  - [x] 32.1 `DependencyMap.test.tsx` — node click opens DetailsPanel (Req 14 AC 2a)
    - Render `DependencyMapPage` with mocked graph data
    - Simulate click on a node
    - Assert `DetailsPanel` is visible and shows the component's name
    - _Requirements: 14.2_

  - [x] 32.2 `FilterToolbar.test.tsx` — type filter hides other-type nodes (Req 14 AC 2b)
    - Render canvas with nodes of types `database` and `api_service`
    - Apply filter for `database`
    - Assert only database nodes are rendered; api_service nodes are hidden
    - _Requirements: 14.2_

  - [x] 32.3 `SimulationIndicator.test.tsx` — indicator appears when simulation active (Req 14 AC 2c)
    - Render `TopBar` with `simulationOverlay=null` → assert indicator hidden
    - Set overlay with a component failure → assert `SimulationActiveIndicator` shows component name
    - _Requirements: 14.2_

  - [x] 32.4 `ResetButton.test.tsx` — reset clears simulation overlay (Req 14 AC 2d)
    - Render `FailureSimulatorPage` with active overlay
    - Mock `POST /scenarios/{id}/reset` → 200
    - Click "Reset Simulation"
    - Assert `simulationOverlay` is null in context
    - Assert affected node styles restored to default
    - _Requirements: 14.2_

  - [x] 32.5 `ApiErrorState.test.tsx` — 500 error shows message not blank panel (Req 14 AC 2e)
    - Render `OverviewPage` with mocked API returning HTTP 500
    - Assert error banner visible with non-empty message
    - Assert no blank/empty panel state
    - _Requirements: 14.2_

  - [x] 32.6 `ScenarioSwitching.test.tsx` — overlay clears on scenario switch (Req 14 AC 2f)
    - Render `TopBar` with two scenarios and an active overlay on scenario A
    - Select scenario B from `ScenarioPicker`
    - Assert `simulationOverlay` cleared from context (no API reset call made)
    - Mock `GET /scenarios/B/simulation` → 204; assert overlay stays null
    - Mock `GET /scenarios/B/simulation` → 200 with data; assert overlay set to B's data
    - Assert no `POST /reset` call was made
    - _Requirements: 14.2_

---

### Group 15: Documentation and Final Verification

- [x] 33. Write final README.md at workspace root
  - Exact Windows commands (no Docker, no cloud credentials):
    ```
    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    ```
    and:
    ```
    cd frontend
    npm install
    npm run dev
    ```
  - Environment variables: `DATABASE_URL`, `CORS_ORIGIN`, `VITE_API_URL`
  - Verification steps: http://localhost:5173, http://localhost:8000/docs,
    http://localhost:8000/openapi.json
  - DB reset: `del backend\impactlens.db` then restart API server
  - Backend tests: `pytest backend/tests/ -v`
  - Frontend tests: `npx vitest --run` from `frontend/`
  - Demo walkthrough section (4 scenarios: Database Failure, Shared Dependency Failure,
    Alternative Path Available, Incomplete Evidence)
  - Known limitations section (no multi-step recovery, no real AWS, no auth, no Docker,
    no light theme, single-worker only, no deletion of simulation history)
  - All demo data labelled as simulated
  - _Requirements: All constraints_

- [x] 34. Final checkpoint — full system verification
  - Run all backend tests: `pytest backend/tests/ -v` — all pass
  - Run all frontend tests: `npx vitest --run` — all pass
  - Verify all 12 Correctness Properties from design.md are covered by tests:
    - Property 1 (DAG equivalence) — covered by `test_dag_equivalence` (PBT)
    - Property 2 (failed-edge subset) — covered by `test_failed_edge_subset` (PBT)
    - Property 3 (alt-path detection) — covered by `test_alternative_path_detection_reporting` (PBT)
    - Property 4 (Impact Score range) — covered by impact engine unit tests
    - Property 5 (DCS independence) — covered by `test_impact_score_unchanged_by_dq_scores`
    - Property 6 (Impact Path coverage) — covered by `build_impact_report` unit tests
    - Property 7 (DQ warning universality) — covered by explanation engine tests
    - Property 8 (staleness warning) — covered by `test_stale_evidence_triggers_staleness_warning`
    - Property 9 (component round-trip) — covered by CRUD tests
    - Property 10 (duplicate name rejection) — covered by `test_api_components.py`
    - Property 11 (recovery non-expansion) — covered by `test_edge_recovery_delta_is_subset_of_original`
    - Property 12 (RFC 7807 compliance) — covered by `test_api_scenarios.py` error cases
  - Verify http://localhost:8000/docs serves OpenAPI UI (Req 9 AC 10)
  - Verify http://localhost:8000/openapi.json is valid JSON (Req 9 AC 10)
  - _Requirements: 14, 9.10_

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; however, they cover
  requirements traceability and correctness verification and are strongly recommended.
- Each task references specific requirements for traceability.
- The implementation runs on Windows without Docker; never use Docker or container commands.
- All demo data is labelled `evidence_source="simulated_demo"` and `confirmation_status="inferred"` —
  it must never be presented to the user as real infrastructure telemetry.
- The Impact Score and Data Confidence Score are always two separate values in every impact report.
  Poor data quality warns the user but never silently reduces the Impact Score.
- The Recovery Planner supports only single-target recovery (direct simulation target);
  multi-step recovery is explicitly out of scope.
- All graph traversal and explanation generation is deterministic and uses no LLM or external AI.
- The Active Simulation Store is in-memory only; it is lost on server restart by design.
- Do not implement a `is_failed` column on the `edges` table — failed-edge state lives only
  in the in-memory `ActiveSimulation` object.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3"] },
    { "id": 1, "tasks": ["1.2", "2.2", "4.1", "4.2"] },
    { "id": 2, "tasks": ["4.3", "5.1", "5.2", "5.3", "5.4", "5.5"] },
    { "id": 3, "tasks": ["5.6", "6.1", "6.2"] },
    { "id": 4, "tasks": ["6.3", "6.4", "7.1", "7.2"] },
    { "id": 5, "tasks": ["7.3", "8.1", "8.2"] },
    { "id": 6, "tasks": ["8.3", "9", "10"] },
    { "id": 7, "tasks": ["11.1", "11.2", "11.3", "11.4"] },
    { "id": 8, "tasks": ["11.5", "12.1"] },
    { "id": 9, "tasks": ["12.2", "13.1", "13.2"] },
    { "id": 10, "tasks": ["13.3", "13.4"] },
    { "id": 11, "tasks": ["13.5", "13.6", "13.7", "14.1"] },
    { "id": 12, "tasks": ["14.2", "15.1", "15.2"] },
    { "id": 13, "tasks": ["15.3", "15.4"] },
    { "id": 14, "tasks": ["16.1", "16.2", "16.3"] },
    { "id": 15, "tasks": ["17.1", "17.2", "17.3"] },
    { "id": 16, "tasks": ["19.1", "19.2", "19.3"] },
    { "id": 17, "tasks": ["20.1", "20.2"] },
    { "id": 18, "tasks": ["21.1", "21.2", "21.3", "21.4"] },
    { "id": 19, "tasks": ["22.1", "22.2"] },
    { "id": 20, "tasks": ["23.1", "23.2", "23.3", "23.4"] },
    { "id": 21, "tasks": ["24.1", "24.2", "24.3", "24.4", "24.5"] },
    { "id": 22, "tasks": ["25.1", "25.2", "26"] },
    { "id": 23, "tasks": ["27.1", "27.2", "27.3"] },
    { "id": 24, "tasks": ["28.1", "28.2", "29", "30.1", "30.2"] },
    { "id": 25, "tasks": ["31"] },
    { "id": 26, "tasks": ["32.1", "32.2", "32.3", "32.4", "32.5", "32.6"] },
    { "id": 27, "tasks": ["33", "34"] }
  ]
}
```
