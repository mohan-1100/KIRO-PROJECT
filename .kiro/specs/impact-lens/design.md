# ImpactLens â€” Technical Design Document

> **Feature**: `impact-lens`
> **Workflow**: Requirements-First
> **Status**: Draft
> **Requirements reference**: `.kiro/specs/impact-lens/requirements.md`

---

## Table of Contents

1. [Overview](#overview)
   - [Architecture Overview](#architecture-overview)
2. [Architecture](#architecture)
   - [Frontend Architecture](#frontend-architecture)
   - [Backend Architecture](#backend-architecture)
3. [Components and Interfaces](#components-and-interfaces)
   - [Graph Engine Design](#graph-engine-design)
   - [Impact Score Formula](#impact-score-formula)
   - [Explanation Engine Design](#explanation-engine-design)
   - [Recovery Engine Design](#recovery-engine-design)
   - [Seed Data Design](#seed-data-design)
   - [Frontend Design Patterns](#frontend-design-patterns)
4. [Data Models](#data-models)
5. [Correctness Properties](#correctness-properties)
6. [Error Handling](#error-handling)
7. [Testing Strategy](#testing-strategy)
   - [Development Setup](#development-setup)
   - [Scope Limitations](#scope-limitations)

---

## Overview

#### Architecture Overview

#### High-Level System Diagram

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        Browser (localhost:5173)                 â”‚
â”‚                                                                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚                    React / Vite Frontend                  â”‚  â”‚
â”‚  â”‚                                                          â”‚  â”‚
â”‚  â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚  â”‚
â”‚  â”‚  â”‚  TopBar  â”‚  â”‚   Sidebar    â”‚  â”‚   DetailsPanel    â”‚  â”‚  â”‚
â”‚  â”‚  â”‚(Scenario â”‚  â”‚  (nav links) â”‚  â”‚  (node/sim info)  â”‚  â”‚  â”‚
â”‚  â”‚  â”‚ Picker)  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚  â”‚
â”‚  â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                            â”‚  â”‚
â”‚  â”‚  Pages: Overview â”‚ DependencyMap (React Flow canvas)     â”‚  â”‚
â”‚  â”‚         FailureSimulator â”‚ IncidentAnalysis              â”‚  â”‚
â”‚  â”‚         RecoveryPlanner  â”‚ InfrastructureInventory       â”‚  â”‚
â”‚  â”‚         SimulationHistory â”‚ SettingsDataQuality          â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                              â”‚ HTTP REST (JSON)                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚
                               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  API_Server (FastAPI, localhost:8000)            â”‚
â”‚                                                                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  Routers: scenarios / components / edges / simulations  â”‚   â”‚
â”‚  â”‚           incidents / data_quality / settings           â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                              â”‚                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚  In-Memory     â”‚  â”‚  Graph_Engine  â”‚  â”‚   Impact_Engine  â”‚  â”‚
â”‚  â”‚  Active Sim    â”‚  â”‚  (NetworkX)    â”‚  â”‚ + Explanation    â”‚  â”‚
â”‚  â”‚  Store (dict)  â”‚  â”‚  graph_builder â”‚  â”‚ + Recovery       â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                              â”‚                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚         DB Layer (SQLite via sqlite3)                   â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                              â”‚                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚                    Seed_Loader                          â”‚   â”‚
â”‚  â”‚  (runs once on startup if DB has no Component records)  â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              SQLite File: impactlens.db                         â”‚
â”‚  Tables: scenarios | components | edges | simulation_history   â”‚
â”‚          settings                                               â”‚
â”‚  No Docker. No cloud credentials. No external DB.              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Module Boundaries and Responsibilities

| Module | Responsibility |
|--------|---------------|
| **Frontend** | Renders the React SPA; owns all UI state (scenario selection, simulation overlay, filter state); communicates with API_Server only via typed HTTP fetch calls; never reads the SQLite file directly |
| **API_Server** | Exposes REST endpoints; validates all inputs via Pydantic; coordinates DB reads/writes; delegates graph traversal to Graph_Engine; owns the in-memory Active Simulation store |
| **Graph_Engine** | Builds a NetworkX DiGraph from DB data + simulation overlay; drives BFS traversal for the Impact_Engine |
| **Impact_Engine** | Receives traversal result from Graph_Engine; computes Impact Score (4-factor formula), Data Confidence Score, severity rankings, and the structured impact report |
| **Explanation_Engine** | Renders human-readable text explanations for each Impact Path using a template registry; no LLM or external AI |
| **Recovery_Engine** | Clones simulation graphs; re-runs BFS for each recovery candidate; computes deltas; ranks recovery options |
| **DB Layer** | Wraps sqlite3; manages table creation; provides typed CRUD helpers; enforces schema constraints |
| **Seed_Loader** | Inserts 4 demo Scenarios and 14 Components on first startup (idempotent â€” skips if Components already exist) |

#### Communication Patterns

- **Frontend â†’ API_Server**: JSON over HTTP/REST. All endpoints are scenario-scoped (e.g., `GET /scenarios/{scenario_id}/graph`). The Frontend reads `scenario_id` from ScenarioPicker state and passes it as a URL path parameter on every call.
- **Active Simulation state**: Stored entirely in a Python `dict` keyed by `scenario_id` in API_Server process memory. Never written to DB. Lost on server restart. Frontend detects absence via `GET /scenarios/{scenario_id}/simulation` returning HTTP 204.
- **DB Persistence**: All baseline graph data (Scenarios, Components, Edges), Simulation_History, and Settings are stored in SQLite and survive server restarts.

#### Technology Justifications

| Technology | Justification |
|-----------|--------------|
| **React + Vite + TypeScript** | Vite provides fast HMR on Windows with no Docker; TypeScript catches API contract mismatches at build time |
| **React Flow** | Purpose-built for interactive directed graphs in the browser; handles pan/zoom/custom nodes natively; integrates cleanly with React state |
| **Tailwind CSS** | Utility-first dark theme; no CSS-in-JS runtime overhead; accessible color + non-color differentiation is straightforward at the component level |
| **Recharts** | Lightweight composable charting library for the data quality distribution chart in Settings |
| **FastAPI** | Async Python API framework; Pydantic integration is first-class; auto-generates OpenAPI docs at `/docs` with no extra work |
| **Pydantic v2** | Validates all request and response bodies; produces structured field-level error messages that map directly to RFC 7807 |
| **NetworkX** | Mature Python graph library; `DiGraph`, `descendants()`, BFS utilities are exactly the primitives needed; proven cycle safety |
| **SQLite (sqlite3)** | Zero-install, zero-config, single-file database; runs on any Windows machine with Python; sufficient for a single-user simulation tool |
| **Hypothesis** | Python property-based testing library; generates arbitrary graphs and inputs for traversal correctness tests (Req 14 AC 3) |

---

## Architecture

See the Architecture Overview subsection below for the system diagram and module breakdown.

### Frontend Architecture

#### Component Tree

```
App
â”œâ”€â”€ AppProviders (ScenarioContext, SimulationContext)
â”‚   â””â”€â”€ Layout
â”‚       â”œâ”€â”€ TopBar
â”‚       â”‚   â”œâ”€â”€ BrandLogo
â”‚       â”‚   â”œâ”€â”€ ScenarioPicker         â† owns scenario_id selection
â”‚       â”‚   â”œâ”€â”€ EnvironmentBadge       â† always "Simulated Demo"
â”‚       â”‚   â””â”€â”€ SimulationActiveIndicator
â”‚       â”œâ”€â”€ Sidebar
â”‚       â”‚   â””â”€â”€ NavLink Ã— 8
â”‚       â”œâ”€â”€ Workspace (react-router outlet)
â”‚       â”‚   â”œâ”€â”€ OverviewPage
â”‚       â”‚   â”œâ”€â”€ DependencyMapPage
â”‚       â”‚   â”‚   â”œâ”€â”€ ReactFlowCanvas
â”‚       â”‚   â”‚   â”‚   â”œâ”€â”€ CustomNode Ã— n  (per ComponentType)
â”‚       â”‚   â”‚   â”‚   â””â”€â”€ CustomEdge Ã— n
â”‚       â”‚   â”‚   â”œâ”€â”€ FilterToolbar
â”‚       â”‚   â”‚   â””â”€â”€ SearchBar
â”‚       â”‚   â”œâ”€â”€ FailureSimulatorPage
â”‚       â”‚   â”œâ”€â”€ IncidentAnalysisPage
â”‚       â”‚   â”œâ”€â”€ RecoveryPlannerPage
â”‚       â”‚   â”œâ”€â”€ InfrastructureInventoryPage
â”‚       â”‚   â”‚   â””â”€â”€ EditableTableRow Ã— n
â”‚       â”‚   â”œâ”€â”€ SimulationHistoryPage
â”‚       â”‚   â””â”€â”€ SettingsDataQualityPage
â”‚       â””â”€â”€ DetailsPanel              â† right-side sliding panel
â”‚           â”œâ”€â”€ ComponentOverviewTab
â”‚           â”œâ”€â”€ ImpactPathsTab
â”‚           â””â”€â”€ DataQualityTab
```

#### State Management

ImpactLens uses **React Context** (no Redux). State is divided into two contexts:

#### ScenarioContext
```typescript
interface ScenarioContextValue {
  scenarios: Scenario[];
  activeScenarioId: string | null;
  setActiveScenarioId: (id: string) => void;
  activeScenario: Scenario | null;
}
```

- Populated on app load from `GET /scenarios`.
- On first load, automatically selects the first scenario (ordered by `created_at` ascending).
- `scenario_id` flows from this context into every API call via a `useApi` hook.

#### SimulationContext
```typescript
interface SimulationContextValue {
  simulationOverlay: SimulationOverlay | null;
  setSimulationOverlay: (overlay: SimulationOverlay | null) => void;
  clearOverlay: () => void;
}

interface SimulationOverlay {
  simId: string;
  failedTargetId: string;
  failedTargetType: 'component' | 'edge';
  failureType: string;
  affectedComponentIds: string[];
  alternativePathComponentIds: string[];
  impactReport: ImpactReport;
}
```

- The overlay is **separate from baseline graph state**.
- When the user switches scenarios, `clearOverlay()` is called without sending `POST /scenarios/{prev_id}/reset`. The previous scenario's server-side simulation state is preserved.
- When a new scenario is selected, `GET /scenarios/{new_id}/simulation` is called; if an Active Simulation exists, `setSimulationOverlay` is called with the returned data.

#### Scenario Selection Data Flow

```
User selects Scenario X in ScenarioPicker
  â†’ setActiveScenarioId(X)
  â†’ SimulationContext.clearOverlay()    [no API reset call]
  â†’ DependencyMapPage fetches GET /scenarios/X/graph
  â†’ DependencyMapPage fetches GET /scenarios/X/simulation
      204 â†’ no overlay
      200 â†’ setSimulationOverlay(response)
  â†’ Canvas re-renders with new baseline + any existing overlay
```

#### React Flow Integration

**Custom node types** â€” one React component per `ComponentType`:

| Component Type | Icon (Lucide) |
|---------------|--------------|
| `web_application` | `Globe` |
| `api_service` | `Zap` |
| `database` | `Database` |
| `cache` | `Layers` |
| `authentication_service` | `Shield` |
| `message_queue` | `MessageSquare` |
| `payment_service` | `CreditCard` |
| `external_api` | `ExternalLink` |
| `load_balancer` | `GitMerge` |

Each custom node renders: Lucide icon, component name, health status badge (text label + distinct icon â€” `CheckCircle` / `AlertTriangle` / `XCircle` / `HelpCircle`; never color-only to ensure accessibility per Req 1 AC 5), criticality pill, and if `confirmation_status === 'unknown'`, a dashed border + `?` badge (Req 7 AC 7).

**Simulation overlay rendering**: When `simulationOverlay` is non-null, styles are:
- Failed target â†’ red ring + `XCircle` icon
- Affected component â†’ amber ring + warning icon
- Alternative path component â†’ blue-dashed ring + info icon
- Unaffected â†’ default style

#### API Client Layer

```typescript
// src/api/client.ts
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new ApiError(response.status, errorBody);
  }
  if (response.status === 204) return null as T;
  return response.json();
}
```

Each resource has a typed module (`src/api/scenarios.ts`, `src/api/simulations.ts`, etc.). React hooks surface `isLoading`, `error`, and `data` states to page components.

---

### Backend Architecture

#### Module Layout

```
backend/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ routers/
â”‚   â”‚   â”œâ”€â”€ scenarios.py
â”‚   â”‚   â”œâ”€â”€ components.py
â”‚   â”‚   â”œâ”€â”€ edges.py
â”‚   â”‚   â”œâ”€â”€ simulations.py
â”‚   â”‚   â”œâ”€â”€ incidents.py
â”‚   â”‚   â”œâ”€â”€ data_quality.py
â”‚   â”‚   â””â”€â”€ settings.py
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ scenario.py
â”‚   â”‚   â”œâ”€â”€ component.py
â”‚   â”‚   â”œâ”€â”€ edge.py
â”‚   â”‚   â”œâ”€â”€ simulation.py
â”‚   â”‚   â”œâ”€â”€ impact_report.py
â”‚   â”‚   â”œâ”€â”€ recovery.py
â”‚   â”‚   â””â”€â”€ common.py          â† RFC 7807 ProblemDetail, shared enums
â”‚   â”œâ”€â”€ db/
â”‚   â”‚   â”œâ”€â”€ connection.py      â† get_db() dependency, PRAGMA foreign_keys=ON
â”‚   â”‚   â”œâ”€â”€ schema.py          â† CREATE TABLE IF NOT EXISTS statements
â”‚   â”‚   â””â”€â”€ crud/
â”‚   â”‚       â”œâ”€â”€ scenarios.py
â”‚   â”‚       â”œâ”€â”€ components.py
â”‚   â”‚       â”œâ”€â”€ edges.py
â”‚   â”‚       â”œâ”€â”€ simulation_history.py
â”‚   â”‚       â””â”€â”€ settings.py
â”‚   â”œâ”€â”€ engine/
â”‚   â”‚   â”œâ”€â”€ active_simulation_store.py
â”‚   â”‚   â”œâ”€â”€ graph_builder.py
â”‚   â”‚   â”œâ”€â”€ impact_engine.py
â”‚   â”‚   â”œâ”€â”€ explanation_engine.py
â”‚   â”‚   â””â”€â”€ recovery_engine.py
â”‚   â””â”€â”€ seed/
â”‚       â”œâ”€â”€ seed_loader.py
â”‚       â””â”€â”€ fixtures/
â”‚           â”œâ”€â”€ components.json
â”‚           â”œâ”€â”€ edges.json
â”‚           â””â”€â”€ scenarios.json
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ conftest.py
â”‚   â”œâ”€â”€ test_impact_engine.py
â”‚   â”œâ”€â”€ test_impact_engine_pbt.py
â”‚   â”œâ”€â”€ test_recovery_engine.py
â”‚   â”œâ”€â”€ test_api_simulations.py
â”‚   â”œâ”€â”€ test_api_components.py
â”‚   â””â”€â”€ test_seed_loader.py
â”œâ”€â”€ requirements.txt
â””â”€â”€ .env
```

#### In-Memory Active Simulation Store

```python
# app/engine/active_simulation_store.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import threading

@dataclass
class ActiveSimulation:
    scenario_id: str
    sim_id: str
    target_type: str       # "component" | "edge"
    target_id: str
    failure_type: str
    impact_report: dict    # cached full report as dict
    created_at: datetime = field(default_factory=datetime.utcnow)

class ActiveSimulationStore:
    """Thread-safe in-memory store keyed by scenario_id."""
    def __init__(self):
        self._store: dict[str, ActiveSimulation] = {}
        self._lock = threading.Lock()

    def set(self, scenario_id: str, sim: ActiveSimulation) -> None:
        with self._lock:
            self._store[scenario_id] = sim

    def get(self, scenario_id: str) -> Optional[ActiveSimulation]:
        with self._lock:
            return self._store.get(scenario_id)

    def clear(self, scenario_id: str) -> None:
        with self._lock:
            self._store.pop(scenario_id, None)

active_sim_store = ActiveSimulationStore()
```

**Thread-safety note**: The dev server runs in a single Uvicorn worker. The `threading.Lock()` guard ensures correctness if async event loop offloads blocking DB calls to a thread pool.

#### Startup Sequence

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.schema import create_tables
from app.seed.seed_loader import run_seed_if_needed

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()          # CREATE TABLE IF NOT EXISTS â€¦
    run_seed_if_needed()     # INSERT demo data if components table is empty
    yield

app = FastAPI(lifespan=lifespan, title="ImpactLens API", version="1.0.0")
```

Startup order: **create DB tables â†’ run Seed_Loader â†’ begin accepting requests**.

---

## Data Models

### SQLite Schema

#### `scenarios`
```sql
CREATE TABLE IF NOT EXISTS scenarios (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT NOT NULL
);
```

#### `components`
```sql
CREATE TABLE IF NOT EXISTS components (
    id                  TEXT PRIMARY KEY,
    scenario_id         TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL,
    criticality         TEXT NOT NULL DEFAULT 'low',
    health_status       TEXT NOT NULL DEFAULT 'unknown',
    last_observed_at    TEXT,
    evidence_source     TEXT NOT NULL DEFAULT 'unknown',
    confirmation_status TEXT NOT NULL DEFAULT 'unknown',
    data_quality_score  INTEGER NOT NULL DEFAULT 50
        CHECK(data_quality_score BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_components_scenario ON components(scenario_id);
```

`ComponentType` enum values: `web_application`, `api_service`, `database`, `cache`, `authentication_service`, `message_queue`, `payment_service`, `external_api`, `load_balancer`

Unique constraint on `(scenario_id, name)` is enforced **case-insensitively at the application layer** in the CRUD helpers (not as a DB constraint, since SQLite's UNIQUE is case-sensitive for TEXT).

#### `edges`
```sql
CREATE TABLE IF NOT EXISTS edges (
    id                    TEXT PRIMARY KEY,
    scenario_id           TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    source_component_id   TEXT NOT NULL REFERENCES components(id),
    target_component_id   TEXT NOT NULL REFERENCES components(id),
    label                 TEXT,
    evidence_source       TEXT NOT NULL DEFAULT 'unknown',
    confirmation_status   TEXT NOT NULL DEFAULT 'unknown',
    last_observed_at      TEXT,
    UNIQUE(scenario_id, source_component_id, target_component_id)
);

CREATE INDEX IF NOT EXISTS idx_edges_scenario   ON edges(scenario_id);
CREATE INDEX IF NOT EXISTS idx_edges_source     ON edges(source_component_id);
CREATE INDEX IF NOT EXISTS idx_edges_target     ON edges(target_component_id);
```

> **No `is_failed` column.** Failed-edge state is ephemeral and lives only in the in-memory `ActiveSimulation` object. This keeps the DB as the single source of truth for baseline topology and prevents simulation state from leaking into persisted records (Req 10 AC 6).

#### `simulation_history`
```sql
CREATE TABLE IF NOT EXISTS simulation_history (
    id                          TEXT PRIMARY KEY,
    scenario_id                 TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    timestamp                   TEXT NOT NULL,
    failed_target_id            TEXT NOT NULL,
    failed_target_type          TEXT NOT NULL,
    failure_type                TEXT NOT NULL,
    directly_affected_count     INTEGER NOT NULL,
    transitively_affected_count INTEGER NOT NULL,
    impact_score                INTEGER NOT NULL CHECK(impact_score BETWEEN 0 AND 100),
    data_confidence_score       INTEGER NOT NULL CHECK(data_confidence_score BETWEEN 0 AND 100),
    status                      TEXT NOT NULL DEFAULT 'open',
    full_report_json            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_simhist_scenario ON simulation_history(scenario_id);
CREATE INDEX IF NOT EXISTS idx_simhist_status   ON simulation_history(status);
```

#### `settings`
```sql
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR IGNORE INTO settings(key, value) VALUES ('freshness_threshold_hours', '72');
```

### ActiveSimulation In-Memory Object

```python
@dataclass
class ActiveSimulation:
    scenario_id:   str       # UUID
    sim_id:        str       # UUID â€” FK to simulation_history.id
    target_type:   str       # "component" | "edge"
    target_id:     str       # UUID of the failed Component or Edge
    failure_type:  str       # "component_unavailable" | "component_degraded" | "dependency_link_unavailable"
    impact_report: dict      # cached full ImpactReport as a dict
    created_at:    datetime  # UTC timestamp
```

### Foreign Key Relationships

```
scenarios (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€< components (many)       via scenario_id
scenarios (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€< edges (many)            via scenario_id
scenarios (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€< simulation_history (many) via scenario_id
components (1) â”€â”€â”€â”€â”€â”€â”€â”€< edges (many)            via source_component_id
components (1) â”€â”€â”€â”€â”€â”€â”€â”€< edges (many)            via target_component_id
```

`PRAGMA foreign_keys = ON;` is issued on every connection in `db/connection.py`.

---

## Components and Interfaces

All error responses are RFC 7807 Problem Detail JSON:
```json
{
  "type": "https://impactlens.local/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Component with id 'abc' not found in scenario 'xyz'.",
  "instance": "/scenarios/xyz/components/abc"
}
```

---

#### Scenario Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/scenarios` | List all Scenarios (ordered by `created_at` ASC) |
| `POST` | `/scenarios` | Create a new Scenario |
| `DELETE` | `/scenarios/{scenario_id}` | Delete Scenario + cascade |

**POST /scenarios** request:
```json
{ "name": "string (required)", "description": "string (optional)" }
```
Errors: `409` duplicate name, `422` missing `name`.

---

#### Graph Endpoint

**GET /scenarios/{scenario_id}/graph** â€” Response 200:
```json
{
  "scenario_id": "uuid",
  "components": [{ "id": "...", "name": "...", "type": "...", "criticality": "...", "health_status": "...",
                   "evidence_source": "...", "confirmation_status": "...", "data_quality_score": 85,
                   "last_observed_at": "2024-01-01T00:00:00Z" }],
  "edges": [{ "id": "...", "source_component_id": "...", "target_component_id": "...",
              "label": "...", "evidence_source": "...", "confirmation_status": "...",
              "last_observed_at": "..." }]
}
```
Errors: `404` scenario not found.

---

#### Component Endpoints (CRUD scoped to scenario)

| Method | URL | Notes |
|--------|-----|-------|
| `POST` | `/scenarios/{scenario_id}/components` | Create; `422` missing required field or out-of-range DQ score; `409` duplicate name |
| `GET` | `/scenarios/{scenario_id}/components` | List all |
| `GET` | `/scenarios/{scenario_id}/components/{id}` | Single; `404` if missing |
| `PUT` | `/scenarios/{scenario_id}/components/{id}` | Full update; `422` validation; `404` if missing |
| `DELETE` | `/scenarios/{scenario_id}/components/{id}` | `409` if has edges; `404` if missing |

**POST/PUT request body**:
```json
{
  "name": "string (required)",
  "type": "ComponentType (required)",
  "criticality": "low|medium|high|critical (required)",
  "health_status": "healthy|degraded|failed|unknown (optional)",
  "last_observed_at": "ISO-8601 (optional)",
  "evidence_source": "enum (optional)",
  "confirmation_status": "enum (optional)",
  "data_quality_score": "0-100 (optional)"
}
```

**DELETE 409** response includes `edge_ids` listing all blocking Edge IDs.

---

#### Edge Endpoints (CRUD scoped to scenario)

| Method | URL | Notes |
|--------|-----|-------|
| `POST` | `/scenarios/{scenario_id}/edges` | Create; `422` self-loop or missing field; `409` duplicate |
| `GET` | `/scenarios/{scenario_id}/edges` | List all |
| `GET` | `/scenarios/{scenario_id}/edges/{id}` | Single |
| `PUT` | `/scenarios/{scenario_id}/edges/{id}` | Update `label` and `evidence_source` only; `source_component_id` and `target_component_id` are immutable |
| `DELETE` | `/scenarios/{scenario_id}/edges/{id}` | Always succeeds if found; `404` if missing |

#### Cross-Scenario Edge Validation

When creating or updating an Edge, the API_Server MUST validate that both `source_component_id` and `target_component_id` belong to the same `scenario_id` as the Edge being created. This prevents cross-scenario dependency relationships that would corrupt graph traversal.

**Validation rule** (applied in the edge CRUD handler before DB insert/update):
```python
# In edges router — POST /scenarios/{scenario_id}/edges
if source_component.scenario_id != scenario_id:
    raise HTTPException(422, detail=f"source_component_id '{source_id}' does not belong to scenario '{scenario_id}'")
if target_component.scenario_id != scenario_id:
    raise HTTPException(422, detail=f"target_component_id '{target_id}' does not belong to scenario '{scenario_id}'")
```

**Error response**: HTTP 422 with RFC 7807 detail identifying which component ID does not belong to the scenario.

**Also applies to**: PUT /scenarios/{scenario_id}/edges/{id} if the endpoint ever allows updating source/target (currently it does not — source and target are immutable after creation, which is an additional guard).

---

#### Simulation Endpoints

#### POST /scenarios/{scenario_id}/simulations
- Executes a simulation, stores Active Simulation in memory, writes to simulation_history, returns full ImpactReport.
- **Request body**:
  ```json
  {
    "scenario_id": "uuid",
    "target_type": "component|edge",
    "target_id": "uuid",
    "failure_type": "component_unavailable|component_degraded|dependency_link_unavailable"
  }
  ```
- **Validation rules**:
  - `target_type=component` â†’ `failure_type` must be `component_unavailable` or `component_degraded`
  - `target_type=edge` â†’ `failure_type` must be `dependency_link_unavailable`
  - Any other combination â†’ `422`
  - `target_id` must belong to `scenario_id` â†’ `404` if not found
- **Response 200**: Full `ImpactReport` (see below).
- **Warning**: If the target Component's baseline `health_status` is already `"failed"`, response includes `"already_failed_warning": true`.

**ImpactReport response structure**:
```json
{
  "sim_id": "uuid",
  "scenario_id": "uuid",
  "failed_target_id": "uuid",
  "failed_target_type": "component",
  "failure_type": "component_unavailable",
  "impact_score": 61,
  "data_confidence_score": 72,
  "score_breakdown": {
    "label": "ImpactLens heuristic v1.0 â€” not an industry standard metric",
    "criticality_score": { "value": 1.0, "weight": 0.35 },
    "reach_score":       { "value": 0.15, "weight": 0.30 },
    "proximity_score":   { "value": 0.4, "weight": 0.20 },
    "isolation_score":   { "value": 0.750, "weight": 0.15 }
  },
  "low_confidence_notice": null,
  "already_failed_warning": false,
  "directly_affected": [
    { "component_id": "uuid", "name": "OrderService", "criticality": "high",
      "severity_contribution": 3.0, "has_alternative_path": false, "possible_alternative_sources": [] }
  ],
  "transitively_affected": [ ... ],
  "impact_paths": [
    {
      "affected_component_id": "uuid",
      "affected_component_name": "OrderService",
      "path_steps": [
        { "component_id": "...", "component_name": "OrderDB", "edge_direction": "â†’" },
        { "component_id": "...", "component_name": "OrderService", "edge_direction": null }
      ],
      "explanation_text": "OrderService depends directly on OrderDB...",
      "has_dq_warning": false,
      "alternative_paths": []
    }
  ],
  "possible_alt_path_components": [
    {
      "component_id": "uuid-inventoryservice",
      "component_name": "InventoryService",
      "possible_alternative_source_names": ["UserDB"],
      "disclosure": "Alternative inbound path detected from UserDB. Operational equivalence is not verified — engineer review required before treating this service as unaffected."
    }
  ],
  "simulated_projection_label": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /scenarios/{scenario_id}/simulations
- Returns Simulation_History for the Scenario in reverse-chronological order.
- **Response 200**: Array of simulation history records.

#### GET /scenarios/{scenario_id}/simulation
- Returns the current Active Simulation state.
- **Response 200**: `ActiveSimulation` object (same structure as `ImpactReport`).
- **Response 204**: No Active Simulation exists.

#### POST /scenarios/{scenario_id}/reset
- Clears Active Simulation from in-memory store.
- Does NOT modify any DB record (not components, not edges, not simulation_history).
- **Response 200**: `{ "detail": "Simulation reset." }`

#### POST /scenarios/{scenario_id}/simulations/{sim_id}/recovery
- Runs projected recovery analysis. Does NOT modify Active Simulation state.
- **Request body**:
  ```json
  { "recovery_type": "component|edge", "recovery_target_id": "uuid" }
  ```
- **Response 200**: Recovery result with `simulated_projection_label: "Simulated Projection"`.
- **Error 400**: Recovery target is not in a failed or degraded state.
- **Error 404**: sim_id or recovery_target_id not found.

**Recovery result structure**:
```json
{
  "simulated_projection_label": "Simulated Projection",
  "recovery_target_id": "uuid",
  "recovery_type": "component",
  "services_recovered": ["uuid1", "uuid2"],
  "services_still_affected": ["uuid3"],
  "services_recovered_count": 2,
  "services_still_affected_count": 1,
  "projected_impact_score": 22,
  "disclosure": "Recovery analysis is a simulated projection. It does not account for configuration, data consistency, capacity, or routing factors not represented in the dependency graph."
}
```

---

#### Data Quality Endpoint

#### GET /scenarios/{scenario_id}/data-quality
- **Response 200**:
  ```json
  {
    "data_completeness_indicator": 67,
    "freshness_threshold_hours": 72,
    "components": [
      { "component_id": "...", "name": "...", "evidence_source": "...",
        "confirmation_status": "...", "data_quality_score": 85,
        "last_observed_at": "...", "is_stale": false, "hours_since_observed": 12 }
    ],
    "edges": [
      { "edge_id": "...", "source_name": "...", "target_name": "...",
        "evidence_source": "...", "confirmation_status": "...",
        "last_observed_at": "...", "is_stale": false }
    ]
  }
  ```

---

#### Incident Endpoints

#### GET /incidents
- Returns all Incidents (Simulation_History records) in reverse-chronological order across all scenarios.
- **Response 200**: Array of `{ id, scenario_id, timestamp, failed_target_id, failed_target_type, failure_type, directly_affected_count, transitively_affected_count, impact_score, data_confidence_score, status }`.

#### PATCH /incidents/{incident_id}
- **Request body**: `{ "status": "resolved" }`
- **Response 200**: Updated Incident.
- **Error 404**: Incident not found.
- **Error 422**: `status` not `"resolved"`.

---

#### Settings Endpoints

#### GET /settings
- **Response 200**: `{ "freshness_threshold_hours": 72 }`

#### PUT /settings
- **Request body**: `{ "freshness_threshold_hours": 48 }`
- **Validation**: value must be integer 1â€“8760.
- **Response 200**: Updated settings object.
- **Error 422**: Value out of range.

---

### Graph Engine Design

#### Graph Representation

ImpactLens uses a **NetworkX `DiGraph`** where:
- Each **node** = a Component ID (UUID string)
- Each **edge** = a directed pair `(source_id, target_id)` where `source_id â†’ target_id` means "target depends on source"

Node attributes stored on each node:
```python
{
  "name": str,
  "criticality_weight": int,   # 1=low, 2=medium, 3=high, 4=critical
  "health_status": str,
  "data_quality_score": int
}
```

Edge attributes stored on each edge:
```python
{
  "edge_id": str,              # UUID from DB
  "is_present": bool           # runtime only â€” False if marked as failed in overlay
}
```

> `is_present` exists only on the in-memory NetworkX graph and is never written to the DB.

#### Edge Direction Convention

Following the Glossary: **A â†’ B means B depends on A**.

In NetworkX terms: `graph.add_edge(A, B)` means "B depends on A". To find all services affected when A fails, the Impact_Engine traverses **successors** of A (the nodes at the head of outgoing edges from A).

Example:
```
OrderDB â†’ OrderService â†’ ShoppingApp
```
If `OrderDB` fails, traversing successors gives `OrderService` (direct), then `ShoppingApp` (indirect).

#### Building the Simulation Graph

```python
# app/engine/graph_builder.py

def build_simulation_graph(
    components: list[Component],
    edges: list[Edge],
    active_sim: Optional[ActiveSimulation]
) -> tuple[nx.DiGraph, set[str], set[str]]:
    """
    Returns (graph, failed_node_ids, failed_edge_ids).
    failed_node_ids: set of component IDs treated as failed
    failed_edge_ids: set of edge IDs treated as absent
    """
    G = nx.DiGraph()

    # Step 1: Add all nodes with attributes
    for component in components:
        G.add_node(component.id,
                   name=component.name,
                   criticality_weight=CRITICALITY_WEIGHTS[component.criticality],
                   health_status=component.health_status,
                   data_quality_score=component.data_quality_score)

    # Step 2: Add all edges with is_present=True
    for edge in edges:
        G.add_edge(edge.source_component_id,
                   edge.target_component_id,
                   edge_id=edge.id,
                   is_present=True)

    failed_node_ids: set[str] = set()
    failed_edge_ids: set[str] = set()

    # Step 3: Apply simulation overlay
    if active_sim:
        if active_sim.target_type == "component":
            if active_sim.failure_type == "component_unavailable":
                # Mark the node as failed; BFS will not traverse through it.
                # All edges incident on this node are logically severed during traversal.
                failed_node_ids.add(active_sim.target_id)
                G.nodes[active_sim.target_id]["health_status"] = "failed"
            elif active_sim.failure_type == "component_degraded":
                # Mark the node as degraded in the overlay.
                # Edges REMAIN traversable — degraded means slower/unreliable, not absent.
                # The node's health_status changes but it is NOT added to failed_node_ids.
                G.nodes[active_sim.target_id]["health_status"] = "degraded"
                # No change to failed_node_ids — BFS continues through this node.
        elif active_sim.target_type == "edge":
            # dependency_link_unavailable: mark only the selected edge as absent.
            # Both endpoint components keep their baseline health_status unchanged.
            failed_edge_ids.add(active_sim.target_id)
            for u, v, data in G.edges(data=True):
                if data.get("edge_id") == active_sim.target_id:
                    G[u][v]["is_present"] = False
                    break

    return G, failed_node_ids, failed_edge_ids
```

#### BFS Traversal Algorithm

The BFS traversal is the core of impact identification. Here it is in pseudocode, then Python:

**Pseudocode**:
```
function find_impacted(graph, failed_node, failed_node_ids, failed_edge_ids):
    affected = {}            # node_id â†’ hop_distance
    queue = deque([(failed_node, 0)])
    visited = {failed_node}

    while queue is not empty:
        current, hop = dequeue from queue

        for each successor S of current in graph:
            edge_data = graph[current][S]

            # Skip failed edges
            if edge_data["is_present"] is False:
                continue

            # Skip: the current node is failed (component_unavailable).
            # BFS reached here but should not propagate further through this node.
            if current in failed_node_ids:
                continue

            if S not in visited:
                visited.add(S)

                # Check if S has a valid alternative path
                if has_alternative_path(graph, S, failed_node_ids, failed_edge_ids, affected):
                    continue   # S is excluded from impacted set

                hop_distance = hop + 1
                affected[S] = hop_distance
                enqueue (S, hop_distance)

    return affected
```

**Python implementation**:
```python
# app/engine/impact_engine.py
from collections import deque
import networkx as nx

def find_impacted_components(
    G: nx.DiGraph,
    failed_node: str,
    failed_node_ids: set[str],
    failed_edge_ids: set[str]
) -> tuple[dict[str, int], dict[str, list[str]]]:
    """
    Returns:
      affected       : {component_id: hop_distance} — components confirmed as impacted.
      possible_alts  : {component_id: [source_id, ...]} — components reachable from the
                       failed node that appear to have an alternative inbound path,
                       reported separately rather than silently excluded.

    Design decision (final):
    A component that has an apparent alternative inbound path is NOT automatically excluded
    from the impacted set. Topology alone is insufficient evidence that a service can
    operate without its failed dependency. Instead:
      - The component IS included in `affected` (conservative: assume impact).
      - Its detected alternative sources are recorded in `possible_alts`.
      - The impact report UI and explanations surface the alternative path as a disclosure,
        not as a guarantee of continued operation.

    This ensures engineers are never misled into thinking a service is safe simply because
    the graph shows another inbound edge. They must verify operational equivalence manually.

    The topology-only limitation and this conservative choice are disclosed in every
    impact report that contains entries in `possible_alts`.
    """
    affected: dict[str, int] = {}
    possible_alts: dict[str, list[str]] = {}
    queue: deque[tuple[str, int]] = deque([(failed_node, 0)])
    visited: set[str] = {failed_node}

    while queue:
        current, hop = queue.popleft()

        for successor in G.successors(current):
            edge_data = G[current][successor]

            # Respect failed edges (dependency_link_unavailable)
            if not edge_data.get("is_present", True):
                continue

            # Do not propagate through a failed (component_unavailable) node
            if current in failed_node_ids:
                continue

            if successor in visited:
                continue

            visited.add(successor)

            # Check for apparent alternative paths (topology only — not operational proof)
            alt_sources = _find_apparent_alternative_sources(
                G, successor, failed_node_ids, affected
            )
            if alt_sources:
                # Record the detected alternative sources for reporting
                possible_alts[successor] = alt_sources
                # Still include in affected — conservative design; topology ≠ operational health

            hop_distance = hop + 1
            affected[successor] = hop_distance
            queue.append((successor, hop_distance))

    return affected, possible_alts
```

#### Failure Type Semantics Summary

| failure_type | target_type | Effect on graph | BFS traversal |
|---|---|---|---|
| `component_unavailable` | component | Node health_status → "failed"; node added to `failed_node_ids` | BFS does not propagate through the failed node; all its outbound edges are blocked; reachable dependants with apparent alternative sources are reported in `possible_alts` but remain in `affected` |
| `component_degraded` | component | Node health_status → "degraded"; NOT added to `failed_node_ids` | BFS propagates normally through the degraded node; only the overlay health indicator changes |
| `dependency_link_unavailable` | edge | Selected edge `is_present` → False; edge ID added to `failed_edge_ids` | BFS skips the failed edge; both endpoint nodes retain their baseline health_status |

**Why this matters**: A `component_degraded` failure records that the component is under stress but still serving traffic. Downstream components may still be reachable through it. A `component_unavailable` failure completely severs the component from the graph, blocking all paths that pass through it.

---

#### Alternative Path Detection Algorithm

The A → B convention means B depends on A. When component F fails, any component D reachable from F via dependant edges is a candidate for impact. D may also have other inbound edges from non-failed sources.

**Design decision**: ImpactLens does NOT automatically exclude D from the impacted set based on topology alone. An alternative inbound edge is detected and *reported separately*, but D remains in the `affected` set. This is the correct conservative choice because:
- Topology does not prove operational equivalence (two databases may hold different data).
- BFS ordering means a source's own impact status may not yet be known when D is first evaluated.
- Engineers need to see all possibly affected services, not a filtered subset based on unverified assumptions.

The function `_find_apparent_alternative_sources` returns a list of source IDs that *appear* to provide an alternative inbound path to a given dependant, based solely on graph topology. The result is recorded in `possible_alts` and surfaced in the impact report as a disclosure notice.

```python
def _find_apparent_alternative_sources(
    G: nx.DiGraph,
    dependant: str,
    failed_node_ids: set[str],
    current_impacted: dict[str, int]
) -> list[str]:
    """
    Returns source IDs that appear to provide alternative inbound paths to 'dependant'.
    Non-empty result means: topology suggests an alternative — engineer review required.
    Empty result means: no topological alternative detected — impact is certain.
    See full docstring in impact_engine.py.
    """
    alternatives = []
    for source in G.predecessors(dependant):
        edge_data = G[source][dependant]
        if not edge_data.get("is_present", True):
            continue
        if source in failed_node_ids:
            continue
        if source in current_impacted:
            continue
        alternatives.append(source)
    return alternatives
```

**What callers receive**: `find_impacted_components` returns `(affected, possible_alts)` where:
- `affected`: all components confirmed as impacted (conservative — includes components with detected alternatives).
- `possible_alts`: dict mapping component ID → list of apparent alternative source IDs, for those in `affected` where topology suggests an alternative.

**Impact report**: Components in `possible_alts` appear in `affected` AND receive an additional annotation in the impact report:
> "Alternative inbound path detected from [source name]. Operational equivalence is not verified — engineer review required before treating this service as unaffected."

This annotation replaces the previous behavior of silently excluding the component from the impacted set.

**Limitations disclosed**:
- Topology-only detection cannot verify capability equivalence.
- BFS ordering means a source not yet processed may not appear in `current_impacted`; the conservative inclusion in `affected` ensures correctness.
- Cycle paths are handled: the visited set prevents re-processing; the `current_impacted` check prevents a node that was later found to be impacted from being treated as an alternative.

#### Correctness Notes

**Cycles**: The visited set prevents infinite loops. A node in a cycle that becomes impacted will appear in `current_impacted` before any later node can use it as an alternative.

**Multiple inbound paths**: All predecessors of a dependant are checked. Any that pass conditions (a), (b), (c) are reported as possible alternatives.

**Failed edges in cycles**: Condition (a) explicitly skips failed edges. A cycle through a failed edge cannot produce a false alternative.

**Ordering limitation**: BFS processes nodes level by level. When D is first encountered, some of D's predecessor nodes may not yet be in `current_impacted` (they are at the same BFS depth or deeper). The conservative design handles this: D is always included in `affected`. The alternative sources list is a best-effort detection based on information available at that BFS step.
#### Cycle Safety

NetworkX `DiGraph` permits cycles. The visited set in the BFS is the guard against infinite loops.

Example cycle: `A â†’ B â†’ C â†’ A`

```
BFS from A:
  visited = {A}
  queue = [(A, 0)]
  
  Process A: successors = [B]
    B not in visited â†’ visited = {A, B} â†’ affected[B] = 1 â†’ queue = [(B, 1)]
  
  Process B: successors = [C]
    C not in visited â†’ visited = {A, B, C} â†’ affected[C] = 2 â†’ queue = [(C, 2)]
  
  Process C: successors = [A]
    A IS in visited â†’ skip  â† cycle safely terminated
  
  queue empty â†’ done
  Result: {B: 1, C: 2}
```

Each node is processed at most once per BFS run, satisfying Req 4 AC 4.

#### Deduplication

The `affected` dict is keyed by `component_id`. If multiple traversal paths reach the same component (possible in graphs with multiple paths), the first path found wins (shortest BFS hop). A component appears at most once in the impact report, satisfying Req 4 AC 10.

---

### Impact Score Formula

#### Formula Reference (Req 4 AC 7)

Step 1 â€” Compute per-factor normalized scores (each 0.0â€“1.0):
```
criticality_score = criticality_weight / 4
reach_score       = min(affected_count, 20) / 20
proximity_score   = 1 / (1 + avg_hop_distance)
isolation_score   = 1 âˆ’ alt_path_ratio
```

Step 2 â€” Weighted sum:
```
raw_score = (criticality_score Ã— 0.35)
          + (reach_score       Ã— 0.30)
          + (proximity_score   Ã— 0.20)
          + (isolation_score   Ã— 0.15)
```

Step 3 â€” Scale and clamp:
```
impact_score = min(100, round(raw_score Ã— 100))
```

#### `alt_path_ratio` Definition

`alt_path_ratio` is defined as:

```
alt_path_ratio = len(possible_alts) / len(affected)
               = (count of components in affected that have at least one detected
                  apparent alternative inbound source)
               / (total count of components in affected)
```

**Numerator**: count of components in `affected` for which `possible_alts[component_id]` is non-empty (i.e., at least one predecessor passed the three conditions).

**Denominator**: total count of components in `affected`.

**Range**: 0.0 (no affected component has any detected alternative) to 1.0 (every affected component has at least one detected alternative).

**Why this is meaningful**: Because `possible_alts` components ARE in the `affected` set (conservative design), `alt_path_ratio` measures the fraction of affected services for which an engineer should prioritise verification — services where the actual impact may be lower than the worst case. A high `alt_path_ratio` means many affected services have unverified potential bypasses; a low ratio means the failure is well-isolated and most impacts are certain.

**Isolation score interpretation**:
- `isolation_score = 1.0` (alt_path_ratio = 0): every affected service has no detected alternative — maximum isolation, full weight to the score.
- `isolation_score = 0.5` (alt_path_ratio = 0.5): half the affected services have detected alternatives — moderate isolation.
- `isolation_score = 0.0` (alt_path_ratio = 1.0): every affected service has a detected alternative — low isolation, minimum contribution to score.

**Python implementation** in `compute_impact_score`:

```python
# isolation_score: fraction of affected components with NO detected alternative path
# possible_alts comes from find_impacted_components() return value
alt_path_count = sum(1 for nid in affected if nid in possible_alts and possible_alts[nid])
alt_path_ratio = alt_path_count / affected_count if affected_count > 0 else 0.0
isolation_score = 1.0 - alt_path_ratio
```

**Note**: In graphs where no component has any non-failed, non-impacted predecessor (a linear chain), `alt_path_ratio = 0.0` and `isolation_score = 1.0`. In graphs with redundant paths, `alt_path_ratio > 0.0` reflects the fraction of services with detected alternatives.
#### Worked Example

**Scenario**: OrderDB (criticality=critical, weight=4) fails with `component_unavailable`.

**Graph**: OrderDB → OrderService → ShoppingApp; OrderDB → ReportingService; UserDB → InventoryService; OrderDB → InventoryService.

BFS from OrderDB identifies:
- OrderService: 1 hop. Predecessors: OrderDB only (failed). `possible_alts = []` → no alternative detected.
- ShoppingApp: 2 hops. Predecessors: OrderService only (now in `affected`). `possible_alts = []` → no alternative.
- ReportingService: 1 hop. Predecessors: OrderDB only (failed). `possible_alts = []` → no alternative.
- InventoryService: 1 hop. Predecessors: OrderDB (failed) AND UserDB (not failed, not impacted). `possible_alts = [UserDB]` → alternative detected. InventoryService **remains in `affected`** (conservative), but `possible_alts[InventoryService] = [UserDB]`.

**Inputs to `compute_impact_score`**:

| Input | Value | Derivation |
|---|---|---|
| `affected` | `{OrderService: 1, ShoppingApp: 2, ReportingService: 1, InventoryService: 1}` | BFS result — all 4 included (conservative) |
| `possible_alts` | `{InventoryService: ["UserDB"]}` | 1 of 4 has a detected alternative |
| `affected_count` | 4 | len(affected) |
| `avg_hop_distance` | (1 + 2 + 1 + 1) / 4 = 1.25 | mean of hop distances |
| `alt_path_count` | 1 | count with non-empty possible_alts entry |
| `alt_path_ratio` | 1 / 4 = 0.25 | alt_path_count / affected_count |
| `crit_weight` | 4 | OrderDB criticality = "critical" → weight 4 |

**Formula computation**:

| Factor | Formula | Value |
|---|---|---|
| `criticality_score` | 4 / 4 | **1.000** |
| `reach_score` | min(4, 20) / 20 | **0.200** |
| `proximity_score` | 1 / (1 + 1.25) | **0.444** |
| `isolation_score` | 1 − 0.25 | **0.750** |
| `raw_score` | (1.000 × 0.35) + (0.200 × 0.30) + (0.444 × 0.20) + (0.750 × 0.15) | — |
| | 0.350 + 0.060 + 0.089 + 0.113 | **0.612** |
| `impact_score` | round(0.612 × 100) | **61** |

**Data Confidence Score** (computed independently):
If OrderService DQ=80, ShoppingApp=90, ReportingService=20, InventoryService=75:
`data_confidence_score = round((80 + 90 + 20 + 75) / 4) = round(66.25) = 66`

Impact Score = **61**. Data Confidence Score = **66**. The DQ score does not affect the Impact Score.

**Impact report for InventoryService** includes the annotation:
> "Alternative inbound path detected from UserDB. Operational equivalence is not verified — engineer review required before treating this service as unaffected."
#### Factor Intuitions

- **criticality_score** (weight 0.35): How important is this component to the business? A `critical` database (weight 4/4 = 1.0) contributes more than a `low` reporting service (1/4 = 0.25). This is the largest weight because business criticality is the most important single indicator of blast radius.

- **reach_score** (weight 0.30): How many downstream services are affected? Capped at 20 to prevent a single massive hub from dominating the score and making it hard to distinguish between a hub with 20 dependants and one with 200. Above 20, the score saturates at 1.0.

- **proximity_score** (weight 0.20): Are the affected services directly connected (proximity â‰ˆ 1.0) or many hops away (proximity â†’ 0)? A component that breaks many nearby services is more severe than one that breaks a few distant ones. The formula `1 / (1 + avg_hop)` asymptotically approaches 0 for very deep graphs.

- **isolation_score** (weight 0.15): Do affected services have backup routes? A score of 1.0 means no affected service has an alternative path (maximum blast radius). A score of 0.0 would mean every affected service has an alternative path (minimal actual impact). This is the lowest weight because the alternative path check is conservative and cannot verify operational equivalence.

#### Edge Failure Impact Score (Req 4 AC 14)

When `failure_type = dependency_link_unavailable`, `criticality_score` uses:
```
criticality_score = max(criticality_weight(source), criticality_weight(target)) / 4
```

All other factors (reach_score, proximity_score, isolation_score) are computed from the resulting impacted set as normal.

#### Python Implementation

```python
# app/engine/impact_engine.py

CRITICALITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3, "critical": 4}

def compute_impact_score(
    G: nx.DiGraph,
    failed_node: str,
    affected: dict[str, int],                      # {component_id: hop_distance}
    possible_alts: dict[str, list[str]],           # {component_id: [alt_source_ids]}
    failure_type: str,
    target_type: str,
    failed_edge_source: Optional[str] = None,
    failed_edge_target: Optional[str] = None
) -> tuple[int, dict]:
    affected_count = len(affected)

    # criticality_score
    if target_type == "edge" and failed_edge_source and failed_edge_target:
        cw_src = G.nodes[failed_edge_source].get("criticality_weight", 1)
        cw_tgt = G.nodes[failed_edge_target].get("criticality_weight", 1)
        crit_weight = max(cw_src, cw_tgt)
    else:
        crit_weight = G.nodes[failed_node].get("criticality_weight", 1)
    criticality_score = crit_weight / 4

    # reach_score
    reach_score = min(affected_count, 20) / 20 if affected_count > 0 else 0.0

    # proximity_score
    if affected_count > 0:
        avg_hop = sum(affected.values()) / affected_count
        proximity_score = 1 / (1 + avg_hop)
    else:
        proximity_score = 0.0

    # isolation_score: fraction of affected components with NO detected alternative path.
    # possible_alts maps component_id → list of apparent alternative source IDs.
    # Components in possible_alts are still in affected[] (conservative design),
    # but their presence signals that operational impact may be lower than worst case.
    alt_path_count = sum(1 for nid in affected if possible_alts.get(nid))
    alt_path_ratio = alt_path_count / affected_count if affected_count > 0 else 0.0
    isolation_score = 1.0 - alt_path_ratio

    raw_score = (
        criticality_score * 0.35
        + reach_score     * 0.30
        + proximity_score * 0.20
        + isolation_score * 0.15
    )
    impact_score = min(100, round(raw_score * 100))

    breakdown = {
        "label": "ImpactLens heuristic v1.0 â€” not an industry standard metric",
        "criticality_score": {"value": round(criticality_score, 4), "weight": 0.35},
        "reach_score":       {"value": round(reach_score, 4),       "weight": 0.30},
        "proximity_score":   {"value": round(proximity_score, 4),   "weight": 0.20},
        "isolation_score":   {"value": round(isolation_score, 4),   "weight": 0.15},
    }

    return impact_score, breakdown

def compute_data_confidence_score(
    G: nx.DiGraph,
    involved_node_ids: list[str]
) -> int:
    if not involved_node_ids:
        return 100
    scores = [G.nodes[nid].get("data_quality_score", 50) for nid in involved_node_ids]
    return round(sum(scores) / len(scores))
```

---

### Explanation Engine Design

#### Template Registry

The explanation engine uses a dict keyed by `(impact_type, has_alternative, has_dq_warning)`:

```python
# app/engine/explanation_engine.py

TEMPLATES = {
    ("direct", False, False): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted."
    ),
    ("direct", True, False): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "An alternative route was detected: {alt_path}. "
        "Operational equivalence has not been verified â€” engineer review recommended."
    ),
    ("direct", False, True): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "{dq_warning}"
    ),
    ("direct", True, True): (
        "{service} depends directly on {failed_component}. "
        "Because {failed_component} is {failure_description}, {service} may be disrupted. "
        "An alternative route was detected: {alt_path}. "
        "Operational equivalence has not been verified â€” engineer review recommended. "
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
        "An alternative route was detected: {alt_path}. "
        "Operational equivalence has not been verified â€” engineer review recommended."
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
        "An alternative route was detected: {alt_path}. "
        "Operational equivalence has not been verified â€” engineer review recommended. "
        "{dq_warning}"
    ),
}
```

#### Failure Description Map

```python
FAILURE_DESCRIPTIONS = {
    "component_unavailable": "unavailable",
    "component_degraded":    "degraded",
    "dependency_link_unavailable": "disconnected (link unavailable)"
}
```

#### Path Rendering

An Impact Path is rendered as component names joined by " â†’ ":

```python
def render_path(path_steps: list[dict]) -> str:
    return " â†’ ".join(step["component_name"] for step in path_steps)
```

#### DQ Warning Formatting

```python
DQ_WARNING_TEMPLATE = (
    "dependency data quality for {component_name} is low "
    "(score: {score}) â€” impact conclusions for this path may be incomplete."
)
```

Triggered when any Component in an Impact Path has `data_quality_score < 50` (the fixed Data Quality Warning Threshold from the Glossary).

#### Explanation Assembly

```python
def build_explanation(
    affected_component_name: str,
    failed_component_name: str,
    failure_type: str,
    path_steps: list[dict],
    alternative_paths: list[list[dict]],
    low_dq_components: list[dict]
) -> str:
    hop_count = len(path_steps) - 1  # path includes failed node as step 0
    impact_type = "direct" if hop_count == 1 else "indirect"
    has_alternative = len(alternative_paths) > 0
    has_dq_warning = len(low_dq_components) > 0

    template = TEMPLATES[(impact_type, has_alternative, has_dq_warning)]

    # Build intermediate chain for indirect impacts
    intermediate_names = [s["component_name"] for s in path_steps[1:-1]]
    intermediate_chain = " â†’ ".join(intermediate_names) if intermediate_names else ""

    # Build alt path strings
    alt_path_str = "; ".join(render_path(ap) for ap in alternative_paths)

    # Build DQ warning string
    dq_warning_str = " ".join(
        DQ_WARNING_TEMPLATE.format(component_name=c["name"], score=c["data_quality_score"])
        for c in low_dq_components
    )

    return template.format(
        service=affected_component_name,
        failed_component=failed_component_name,
        failure_description=FAILURE_DESCRIPTIONS[failure_type],
        intermediate_chain=intermediate_chain,
        alt_path=alt_path_str,
        dq_warning=dq_warning_str,
    )
```

---

### Recovery Engine Design

#### Recovery for Component-Failure Simulations

```python
# app/engine/recovery_engine.py

def compute_recovery_options(
    G: nx.DiGraph,
    active_sim: ActiveSimulation,
    original_impacted: dict[str, int],
    all_components: list[Component]
) -> list[RecoveryOption]:
    """
    For component failures: enumerate all failed/degraded components as candidates.
    For edge failures: one candidate â€” restore the failed edge.
    """
    options = []

    if active_sim.target_type == "component":
        # Enumerate all failed or degraded components in the simulation
        candidates = [
            c for c in all_components
            if c.health_status in ("failed", "degraded")
            or c.id == active_sim.target_id
        ]

        for candidate in candidates:
            # Clone graph, restore candidate to healthy
            G_copy = G.copy()
            nx.set_node_attributes(G_copy, {candidate.id: {"health_status": "healthy"}})
            failed_nodes_copy = set()  # candidate is no longer failed

            # Re-run BFS
            post_recovery_impacted, post_recovery_alts = find_impacted_components(
                G_copy, active_sim.target_id, failed_nodes_copy, set()
            )

            services_recovered = set(original_impacted) - set(post_recovery_impacted)
            services_still_affected = set(post_recovery_impacted)

            # Re-compute projected impact score
            projected_score, _ = compute_impact_score(
                G_copy, active_sim.target_id, post_recovery_impacted,
                post_recovery_alts, active_sim.failure_type, active_sim.target_type
            )

            options.append(RecoveryOption(
                recovery_target_id=candidate.id,
                recovery_type="component",
                services_recovered=list(services_recovered),
                services_still_affected=list(services_still_affected),
                projected_impact_score=projected_score,
            ))

    elif active_sim.target_type == "edge":
        # One candidate: restore the failed edge in a temporary graph copy.
        # The original G and active_sim are NEVER modified.
        G_copy = G.copy()

        # Find the edge endpoints in the copy and restore is_present
        edge_source: Optional[str] = None
        edge_target: Optional[str] = None
        for u, v, data in G_copy.edges(data=True):
            if data.get("edge_id") == active_sim.target_id:
                G_copy[u][v]["is_present"] = True
                edge_source = u
                edge_target = v
                break

        if edge_source is None:
            # Edge not found in graph copy — return empty options
            return []

        # Compute the impacted set on the RESTORED graph, starting from edge_source.
        # This represents the remaining impact after the edge is back in service.
        post_recovery_impacted, post_recovery_alts = find_impacted_components(
            G_copy,
            failed_node=edge_source,
            failed_node_ids=set(),       # no component is failed in recovery projection
            failed_edge_ids=set()        # no edges are failed — we restored the only one
        )

        # Recovery delta: what was affected before that is no longer affected after restoring the edge.
        # original_impacted comes from the active simulation (the FULL impacted set with the edge failed).
        # post_recovery_impacted is the impacted set computed on the graph WITH the edge restored.
        # services_recovered = components that are in original_impacted but NOT in post_recovery_impacted.
        services_recovered = set(original_impacted.keys()) - set(post_recovery_impacted.keys())
        services_still_affected = set(post_recovery_impacted.keys())

        # Recompute projected impact score using the post-recovery impacted set
        projected_score, _ = compute_impact_score(
            G_copy,
            failed_node=edge_source,
            affected=post_recovery_impacted,
            possible_alts=post_recovery_alts,
            failure_type=active_sim.failure_type,
            target_type="edge",
            failed_edge_source=edge_source,
            failed_edge_target=edge_target
        )

        options.append(RecoveryOption(
            recovery_target_id=active_sim.target_id,
            recovery_type="edge",
            services_recovered=list(services_recovered),
            services_recovered_count=len(services_recovered),
            services_still_affected=list(services_still_affected),
            services_still_affected_count=len(services_still_affected),
            projected_impact_score=projected_score,
        ))

**Edge recovery delta semantics**: `services_recovered` = components that were in `original_impacted` (the active simulation's impacted set, computed with the edge failed) that are NOT in `post_recovery_impacted` (the impacted set computed on the graph with the edge restored). This is a true before/after difference — it does not count all of edge_source's dependants as recovered, only those that would no longer be reachable once the edge is back.

**Example**: Edge A→B is failed. original_impacted = {B, C, D}. After restoring A→B, post_recovery_impacted = {B} (B is still reachable from A's other dependencies). services_recovered = {C, D}. The recovery projection correctly identifies C and D as the services that benefit from restoring the edge.
    # Rank by number of services recovered, descending
    options.sort(key=lambda o: len(o.services_recovered), reverse=True)
    return options
```

#### Delta Display

Each `RecoveryOption` contains:
- `services_recovered_count` = `len(services_recovered)`
- `services_still_affected_count` = `len(services_still_affected)`
- The Frontend displays these in the Recovery Planner table (Req 6 AC 5)

#### No Additional Recovery Note (Req 6 AC 7)

When `services_recovered` is empty for a candidate, the Frontend renders a "No additional services recovered" notice for that row. The API still returns the result â€” the notice is a Frontend concern.

#### Active Simulation Preservation

The `POST .../recovery` endpoint guarantees that the active simulation is never mutated:

1. It reads the Active Simulation from `active_sim_store.get(scenario_id)` — read-only access.
2. It calls `compute_recovery_options(G, active_sim, ...)` which only works on `G.copy()` (deep clone) — the original `G` is never modified.
3. It returns the `RecoveryOption` list.
4. It does **not** call `active_sim_store.set()` or `active_sim_store.clear()`.

A subsequent `GET /scenarios/{scenario_id}/simulation` will return the same unchanged Active Simulation.

**No DB mutations**: Neither the edges table nor any other table is modified during recovery analysis. The `is_present` flag manipulation occurs only in the in-memory `G_copy` clone.

**Isolation test**: The test `test_recovery_does_not_mutate_active_simulation` verifies this by:
1. Starting a simulation and recording the initial active simulation state.
2. Calling the recovery endpoint.
3. Fetching `GET /scenarios/{scenario_id}/simulation` and asserting it equals the initial state.

---

### Seed Data Design

#### Components (14 total, 9 distinct types covered)

| # | Name | Type | Criticality | Health | Evidence Source | DQ Score | Notes |
|---|------|------|-------------|--------|-----------------|----------|-------|
| 1 | ShoppingApp | `web_application` | critical | healthy | simulated_demo | 90 | |
| 2 | APIGateway | `load_balancer` | critical | healthy | simulated_demo | 88 | |
| 3 | OrderService | `api_service` | high | healthy | simulated_demo | 82 | |
| 4 | PaymentService | `api_service` | critical | healthy | simulated_demo | 85 | |
| 5 | UserService | `api_service` | high | healthy | simulated_demo | 80 | |
| 6 | AuthService | `authentication_service` | critical | healthy | simulated_demo | 92 | |
| 7 | OrderDB | `database` | critical | healthy | simulated_demo | 88 | |
| 8 | PaymentDB | `database` | critical | healthy | simulated_demo | 90 | |
| 9 | UserDB | `database` | high | healthy | simulated_demo | 84 | |
| 10 | SessionCache | `cache` | medium | healthy | simulated_demo | 75 | |
| 11 | NotificationQueue | `message_queue` | low | healthy | simulated_demo | 70 | |
| 12 | PaymentProviderAPI | `external_api` | high | healthy | simulated_demo | 65 | |
| 13 | ReportingService | `api_service` | low | healthy | simulated_demo | 20 | Stale evidence, DQ=20 â€” triggers DQ warning |
| 14 | InventoryService | `api_service` | medium | healthy | simulated_demo | 78 | Has alt path via OrderDB |

All seed Components have `confirmation_status = "inferred"` and `evidence_source = "simulated_demo"` (Req 7 AC 8). ReportingService has `last_observed_at` set to >72 hours before seed time, making it stale under the default threshold.

#### Edges (dependency relationships)

Using `A â†’ B` convention (B depends on A):

```
APIGateway       â†’ ShoppingApp
OrderService     â†’ ShoppingApp
PaymentService   â†’ ShoppingApp
UserService      â†’ ShoppingApp
AuthService      â†’ OrderService
AuthService      â†’ PaymentService
AuthService      â†’ UserService
OrderDB          â†’ OrderService
PaymentDB        â†’ PaymentService
UserDB           â†’ UserService
SessionCache     â†’ AuthService
NotificationQueue â†’ OrderService
PaymentProviderAPI â†’ PaymentService
UserDB           â†’ InventoryService    (primary path)
OrderDB          â†’ InventoryService    (alternative path)
OrderDB          â†’ ReportingService
```

#### Four Demo Scenarios

Each Scenario is a named copy of the above 14 components and 16 edges.

#### Scenario A â€” "Database Failure"
- **Simulation target**: `OrderDB` â†’ `component_unavailable`
- **Expected impacted set**:
  - Direct: `OrderService`, `ReportingService`
  - Via OrderService: `ShoppingApp` (indirect, 2 hops), `NotificationQueue` path â†’ `OrderService` direct
  - InventoryService has alternative path via `UserDB` â†’ not impacted
- **DQ effect**: ReportingService DQ=20 â†’ uncertainty annotation on its explanation path

#### Scenario B â€” "Shared Dependency Failure"
- **Simulation target**: `AuthService` â†’ `component_unavailable`
- **Expected impacted set**:
  - Direct: `OrderService`, `PaymentService`, `UserService`
  - Via those: `ShoppingApp` (indirect, 2 hops)
  - SessionCache â†’ AuthService path severed at AuthService
- **Demonstrates**: One shared dependency affecting multiple independent consumers simultaneously

#### Scenario C â€” "Alternative Path Available"
- **Simulation target**: `UserDB` â†’ `component_unavailable`
- **Expected impacted set**:
  - Direct: `UserService`
  - Via UserService: `ShoppingApp` (indirect)
  - `InventoryService`: has alternative inbound edge from `OrderDB` (non-failed) â†’ **excluded from impacted set**
- **Demonstrates**: The Alternative Path exclusion rule; report includes disclosure notice

#### Scenario D â€” "Incomplete Evidence"
- **Simulation target**: `OrderDB` â†’ `component_unavailable`
- **Expected behavior**: Same traversal as Scenario A, but ReportingService (DQ=20, stale) triggers:
  - Uncertainty annotation on its impact path explanation
  - Staleness warning (>72h since last_observed_at)
  - Low Data Confidence Score in the report
- **Demonstrates**: Data quality warnings and their separation from the Impact Score

#### Seed Loader Logic

```python
# app/seed/seed_loader.py

def run_seed_if_needed() -> None:
    """Idempotent: only runs if the components table is empty."""
    db = get_db_connection()
    count = db.execute("SELECT COUNT(*) FROM components").fetchone()[0]
    if count > 0:
        return  # Already seeded â€” do nothing (Req 8 AC 3)

    with open("app/seed/fixtures/scenarios.json") as f:
        scenarios = json.load(f)
    with open("app/seed/fixtures/components.json") as f:
        components = json.load(f)
    with open("app/seed/fixtures/edges.json") as f:
        edges = json.load(f)

    for scenario in scenarios:
        db.execute("INSERT INTO scenarios VALUES (?, ?, ?, ?)", ...)
    for component in components:
        db.execute("INSERT INTO components VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ...)
    for edge in edges:
        db.execute("INSERT INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ...)

    db.commit()
```

---

### Frontend Design Patterns

#### Dark Theme

Tailwind CSS dark palette:

| Purpose | Tailwind class |
|---------|---------------|
| Page background | `bg-slate-950` |
| Card / panel background | `bg-slate-900` |
| Elevated surface | `bg-slate-800` |
| Border | `border-slate-700` |
| Primary text | `text-slate-100` |
| Secondary text | `text-slate-400` |
| Accent / interactive | `text-blue-400`, `bg-blue-500` |
| Healthy status | `text-emerald-400` + `CheckCircle` icon |
| Degraded status | `text-amber-400` + `AlertTriangle` icon |
| Failed status | `text-red-400` + `XCircle` icon |
| Unknown status | `text-slate-400` + `HelpCircle` icon |

Health status is communicated via **both color and icon** (Req 1 AC 5), never by color alone.

#### DetailsPanel

The right-side DetailsPanel is a sliding panel triggered by node click or simulation result selection.

Structure:
```
DetailsPanel (slides in from right, w-96)
â”œâ”€â”€ Header: component name + close button
â”œâ”€â”€ Tabs: [Overview | Impact Paths | Data Quality]
â”‚
â”œâ”€â”€ Overview tab:
â”‚   â”œâ”€â”€ Type badge + icon
â”‚   â”œâ”€â”€ Health status badge (icon + label)
â”‚   â”œâ”€â”€ Criticality badge
â”‚   â”œâ”€â”€ Evidence source
â”‚   â”œâ”€â”€ Confirmation status
â”‚   â”œâ”€â”€ Last observed (with staleness indicator if stale)
â”‚   â””â”€â”€ Data Quality Score (progress bar)
â”‚
â”œâ”€â”€ Impact Paths tab (only shown when simulation active):
â”‚   â””â”€â”€ ImpactPathEntry Ã— n
â”‚       â”œâ”€â”€ Collapsed by default if > 3 paths (Req 5 AC 6)
â”‚       â”œâ”€â”€ Expanded by default if â‰¤ 3 paths
â”‚       â””â”€â”€ On click: highlight path on canvas (Req 5 AC 7)
â”‚
â””â”€â”€ Data Quality tab:
    â”œâ”€â”€ DQ score gauge
    â”œâ”€â”€ Evidence source
    â””â”€â”€ Uncertainty notice (if confirmation_status = "unknown")
```

#### Error States and Loading States

- **Error boundaries**: each Page component is wrapped in a `<PageErrorBoundary>` that catches thrown errors and renders an inline error banner with a retry button.
- **API errors**: the `useApiError` hook converts `ApiError` objects into typed error state; each data-fetch hook exposes `{ data, isLoading, error, retry }`.
- **Skeleton loaders**: graph canvas shows a pulsing placeholder grid during initial load; tables show skeleton rows.

#### Filter and Search Performance

Filters (type, health status, criticality) and search are applied in the Frontend on the in-memory node list â€” no API call is made for filter changes. This guarantees the â‰¤500ms response time requirement (Req 1 AC 7â€“10) because it is a pure client-side operation on the already-loaded graph data.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system â€” essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

---

### Property 1: DAG traversal equivalence

*For any* randomly generated directed acyclic graph with no failed edges and no components with valid alternative paths, and any designated failed node, the set of impacted components returned by the Impact_Engine SHALL equal exactly the set returned by `nx.descendants(graph, failed_node)`.

**Validates: Requirements 4.1, 4.4, 14.3**

---

### Property 2: Failed-edge subset monotonicity

*For any* valid graph and any designated failed node, removing any single edge from the graph before running the Impact_Engine SHALL produce an impacted set that is a subset of (or equal to) the impacted set when that edge is present. The impacted set SHALL NOT grow as a result of removing an edge.

**Validates: Requirements 4.5, 14.3**

---

### Property 3: Alternative-path detection reporting

*For any* valid graph, adding a new valid inbound path to a Dependant that bypasses the failed component (where the source of that path is not a failed node and not itself in the impacted set) SHALL result in that Dependant being added to `possible_alts` in the impact report. The Dependant SHALL still appear in the `affected` set (conservative design). The `alt_path_ratio` SHALL be greater than or equal to its value before the path was added.

**Validates: Requirements 4.3, 14.3**

---

### Property 4: Impact Score range invariant

*For any* valid graph, any failed node, and any failure type, the Impact Score computed by the Impact_Engine SHALL always be an integer in the closed range [0, 100].

**Validates: Requirements 4.7**

---

### Property 5: Data Confidence Score independence

*For any* valid graph and any designated failed node, the Impact Score SHALL be identical whether the involved components have `data_quality_score` of 0 or 100. Only the Data Confidence Score changes; the Impact Score reflects graph topology and criticality alone.

**Validates: Requirements 4.13, 14.1**

---

### Property 6: Impact Path coverage

*For any* simulation result, every component in the impacted set SHALL have at least one Impact Path entry in the impact report. No component in the impacted set may be left without an explanation.

**Validates: Requirements 5.1**

---

### Property 7: DQ warning annotation universality

*For any* impact path containing a component with `data_quality_score < 50`, the explanation text for that path SHALL contain the uncertainty notice string for that component. This must hold for any combination of graph topology and DQ scores.

**Validates: Requirements 5.5, 7.11**

---

### Property 8: Staleness warning universality

*For any* component with `last_observed_at` older than the configured Freshness Threshold, any impact report referencing that component SHALL include a staleness warning identifying the component by name and elapsed hours. This must hold for any threshold value between 1 and 8760 hours and any timestamp.

**Validates: Requirements 7.3**

---

### Property 9: Component creation round-trip

*For any* valid component data payload, creating a component via the API and then retrieving it SHALL return data equivalent to the original payload. The component SHALL be persisted faithfully and retrievable by ID.

**Validates: Requirements 2.1, 9.1**

---

### Property 10: Duplicate name rejection universality

*For any* existing component name in a scenario, submitting a new-component form with that name in any case permutation (e.g., "orderdb", "OrderDB", "ORDERDB") SHALL be rejected with a 409 conflict. The duplicate detection is case-insensitive.

**Validates: Requirements 2.3**

---

### Property 11: Recovery set non-expansion

*For any* active simulation and any recovery candidate, the set of services still affected after the recovery projection SHALL be a subset of (or equal to) the original impacted set. Recovery SHALL NOT add new services to the impacted set. Additionally, the active simulation state returned by `GET /scenarios/{scenario_id}/simulation` SHALL be identical before and after any call to the recovery endpoint.

**Validates: Requirements 6.3**

---

### Property 12: Error response RFC 7807 compliance

*For any* invalid request to the API (missing required field, out-of-range value, duplicate constraint violation, or invalid enum value), the response body SHALL be a valid RFC 7807 Problem Detail JSON object containing at minimum the fields `type`, `title`, `status`, and `detail`.

**Validates: Requirements 9.9**

---

## Error Handling

### API Error Response Format (RFC 7807)

```json
{
  "type": "https://impactlens.local/errors/{error_code}",
  "title": "Human-readable title",
  "status": 422,
  "detail": "Specific description of what went wrong",
  "instance": "/scenarios/abc/components"
}
```

Implemented via a custom FastAPI exception handler:

```python
# app/models/common.py
class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str

# app/main.py
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ProblemDetail(
            type=f"https://impactlens.local/errors/{exc.status_code}",
            title=exc_titles.get(exc.status_code, "Error"),
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
        ).model_dump()
    )
```

### Error Code Reference

| HTTP Status | Trigger | Example |
|------------|---------|---------|
| `400` | Invalid recovery candidate (not failed/degraded) | Recovery requested for a healthy component |
| `404` | Missing resource | Component ID not found in scenario |
| `409` | Duplicate constraint or referential conflict | Component name already exists; delete component with edges |
| `422` | Pydantic validation failure | Missing required field; DQ score out of 0â€“100 range; invalid enum; self-loop edge; invalid target_type+failure_type combination |
| `500` | Unexpected graph engine error | NetworkX internal error (wrapped) |

### Frontend Error Handling

The `useApiError` hook:
```typescript
function useApiError(error: ApiError | null): ErrorDisplay | null {
  if (!error) return null;
  return {
    message: error.detail ?? 'An unexpected error occurred.',
    retryable: error.status >= 500 || error.status === 0,
  };
}
```

Every page that fetches data:
1. Shows a skeleton loader during fetch
2. On success: renders data
3. On error: renders inline error banner with the `detail` field from the RFC 7807 response + a retry button where applicable (Req 12 AC 7)

---

## Testing Strategy

### Backend Test Structure

```
backend/tests/
â”œâ”€â”€ conftest.py                    â† in-memory SQLite fixture, test graph factory (5-node: Aâ†’Bâ†’C, Aâ†’D, Bâ†’D)
â”œâ”€â”€ test_impact_engine.py          â† unit tests for Req 14 AC 1 scenarios aâ€“s
â”œâ”€â”€ test_impact_engine_pbt.py      â† Hypothesis PBT for Req 14 AC 3 aâ€“c
â”œâ”€â”€ test_recovery_engine.py        â† recovery scenarios
â”œâ”€â”€ test_api_simulations.py        â† FastAPI TestClient, simulation endpoint
â”œâ”€â”€ test_api_components.py         â† CRUD validation, 422/409 responses
â””â”€â”€ test_seed_loader.py            â† idempotency, 4 scenarios, 14 components
```

**Standard test graph** (used across unit tests):

```
A â†’ B â†’ C
A â†’ D
B â†’ D
```

Properties of this graph:
- A is the root; C is a leaf; D has two inbound paths (A and B)
- Failing A: B and C and D are impacted (D has alternative path via Aâ†’D when B is the failed node, but not when A is the failed node)
- Failing B: C is impacted; D has alternative path via Aâ†’D â†’ excluded from impacted set
- No cycles (used for simple unit tests; cycle tests use a separate fixture)

### Pytest Unit Test Coverage (Req 14 AC 1)

Each scenario maps to one or more test functions in `test_impact_engine.py`:

| Scenario | Test function |
|----------|-------------|
| a. Direct dependant identification | `test_direct_dependant_identified` |
| b. Indirect dependant identification | `test_indirect_dependant_identified` |
| c. Unaffected component exclusion | `test_unaffected_component_excluded` |
| d. Alternative path exclusion | `test_alternative_path_excludes_component` |
| e. Cycle safety | `test_cycle_does_not_infinite_loop` |
| f. Failed-edge handling | `test_failed_edge_excluded_from_traversal` |
| g. Unknown-status handling | `test_unknown_status_propagates_uncertainty` |
| h. Stale evidence warning | `test_stale_evidence_triggers_staleness_warning` |
| i. Impact Score ranking | `test_higher_criticality_yields_higher_score` |
| j. Explanation correctness | `test_two_hop_explanation_matches_template` |
| k. Recovery comparison | `test_recovery_highest_downstream_recovers_more` |
| l. Invalid edit rejection | `test_missing_required_field_returns_422` |
| m. Scenario reset | `test_reset_clears_active_simulation` |
| n. Deduplication | `test_multi_path_component_appears_once` |
| o. Failed-edge traversal | `test_failed_edge_traversal_semantics` |
| p. Data Confidence Score independence | `test_impact_score_unchanged_by_dq_scores` |
| q. Simulation endpoint validation | `test_invalid_failure_type_combination_returns_422` |
| r. Save as Scenario | `test_save_as_scenario_copies_baseline_only` |
| s. Recovery for edge failure | `test_edge_failure_recovery_offers_one_option` |

#### Additional Test Cases (from Design Review)

Add these test cases to the appropriate test files:

**`test_impact_engine.py`** — failure type and alternative path tests:
- `test_component_unavailable_blocks_traversal`: graph A→B→C, A fails with `component_unavailable`. Assert B and C are in `affected`. Assert A is in `failed_node_ids`.
- `test_component_degraded_traversal_continues`: graph A→B→C, A fails with `component_degraded`. Assert B and C are in `affected`. Assert A is NOT in `failed_node_ids`.
- `test_dependency_link_unavailable_blocks_edge`: graph A→B→C, edge A→B is failed. Assert B and C are NOT in `affected`. Assert A's health_status is unchanged.
- `test_alternative_path_component_still_in_affected`: graph where D has two predecessors (A and X), A fails. Assert D is in `affected`. Assert D is in `possible_alts` with X as a source.
- `test_alternative_path_with_impacted_source_excluded`: graph A→B→D, A→X→D. A fails. B is impacted (1 hop). X is NOT impacted. At BFS time for D: B is in current_impacted, X is not. Assert D is in `affected`. Assert D is in `possible_alts` with X listed (not B, since B is impacted).
- `test_no_alternative_path_when_all_sources_impacted`: graph A→B→D, A→C→D. A fails. B and C are both impacted. Assert D is in `affected`. Assert D is NOT in `possible_alts` (both its predecessors are impacted).
- `test_alt_path_ratio_nonzero_when_alternatives_exist`: for a graph where at least one affected component has a detected alternative, assert `alt_path_ratio > 0.0` and `isolation_score < 1.0`.
- `test_alt_path_ratio_zero_when_no_alternatives`: linear chain graph with no alternative paths, assert `alt_path_ratio = 0.0` and `isolation_score = 1.0`.
- `test_data_confidence_score_independence`: same graph, same failed node, different DQ scores. Assert Impact Score is identical in both runs.

**`test_api_components.py`** and **`test_api_simulations.py`** — cross-scenario validation:
- `test_edge_cross_scenario_rejected`: create two scenarios (A and B) each with one component. Attempt to create an edge in scenario A using a `target_component_id` from scenario B. Assert HTTP 422 with detail identifying the invalid component ID.
- `test_simulation_target_wrong_scenario_rejected`: attempt to run a simulation in scenario A using a `target_id` that belongs to scenario B. Assert HTTP 404.

**`test_recovery_engine.py`** — edge recovery delta tests:
- `test_edge_recovery_delta_is_subset_of_original`: after edge recovery, `post_recovery_impacted ⊆ original_impacted` (recovery never expands impact).
- `test_edge_recovery_services_recovered_correct`: graph A→B→C, edge A→B failed. original_impacted = {B, C}. After restoring A→B, post_recovery_impacted = {}. Assert services_recovered = {B, C}.
- `test_edge_recovery_partial_recovery`: graph A→B→C, A also connects to B via a second path that was never failed. After restoring a failed edge A→C, post_recovery_impacted may still contain B if B has no other impacting path. Assert services_recovered only contains components not in post_recovery_impacted.
- `test_recovery_does_not_mutate_active_simulation`: run simulation, call recovery, fetch active simulation via GET endpoint, assert unchanged.
- `test_recovery_does_not_mutate_baseline_graph`: after `compute_recovery_options`, assert original G's edges all have `is_present=True` for non-simulation-failed edges (no mutation to original graph object).
### Hypothesis Property-Based Tests (Req 14 AC 3)

```python
# backend/tests/test_impact_engine_pbt.py
from hypothesis import given, settings
from hypothesis import strategies as st
import networkx as nx
from app.engine.impact_engine import find_impacted_components

@given(st.data())
@settings(max_examples=200)
def test_dag_equivalence(data):
    """Property 1: DAG equivalence â€” impacted set equals nx.descendants."""
    G = data.draw(dag_strategy())   # generates random DAGs
    if len(G.nodes) == 0:
        return
    failed_node = data.draw(st.sampled_from(list(G.nodes)))
    # Run Impact_Engine (returns tuple of affected, possible_alts)
    impacted, _ = find_impacted_components(G, failed_node, set(), set())
    # Compare with NetworkX ground truth
    expected = nx.descendants(G, failed_node)
    assert set(impacted.keys()) == expected

@given(st.data())
@settings(max_examples=200)
def test_failed_edge_subset(data):
    """Property 2: Removing an edge never grows the impacted set."""
    G = data.draw(graph_strategy())
    if len(G.edges) == 0:
        return
    failed_node = data.draw(st.sampled_from(list(G.nodes)))
    edge_to_remove = data.draw(st.sampled_from(list(G.edges(data=True))))
    u, v, edge_data = edge_to_remove

    original, _ = find_impacted_components(G, failed_node, set(), set())

    # Mark edge as failed
    G_with_failed_edge = G.copy()
    G_with_failed_edge[u][v]["is_present"] = False
    with_failed, _ = find_impacted_components(G_with_failed_edge, failed_node, set(), {edge_data.get("edge_id","x")})

    assert set(with_failed.keys()).issubset(set(original.keys()))

@given(st.data())
@settings(max_examples=200)
def test_alternative_path_detection_reporting(data):
    """Property 3: Adding a bypass path adds the dependant to possible_alts (conservative inclusion).
    
    The dependant remains in affected (conservative design).
    The alt_path_ratio is >= its value before the bypass was added.
    """
    G = data.draw(graph_strategy())
    if len(G.nodes) < 3:
        return
    failed_node = data.draw(st.sampled_from(list(G.nodes)))
    other_nodes = [n for n in G.nodes if n != failed_node]
    if len(other_nodes) < 2:
        return
    bypass_source, bypass_target = data.draw(
        st.lists(st.sampled_from(other_nodes), min_size=2, max_size=2, unique=True)
    )

    original_affected, original_alts = find_impacted_components(G, failed_node, set(), set())
    original_alt_ratio = len(original_alts) / len(original_affected) if original_affected else 0.0

    # Add bypass edge
    G_with_bypass = G.copy()
    if not G_with_bypass.has_edge(bypass_source, bypass_target):
        G_with_bypass.add_edge(bypass_source, bypass_target, is_present=True)

    bypass_affected, bypass_alts = find_impacted_components(G_with_bypass, failed_node, set(), set())
    bypass_alt_ratio = len(bypass_alts) / len(bypass_affected) if bypass_affected else 0.0

    # bypass_target, if it was reached from failed_node and bypass_source is not impacted,
    # should now appear in bypass_alts
    if bypass_target in bypass_affected and bypass_source not in bypass_affected:
        assert bypass_target in bypass_alts, \
            f"{bypass_target} should be in possible_alts since {bypass_source} is a valid alternative"

    # alt_path_ratio should not decrease as a result of adding a bypass path
    assert bypass_alt_ratio >= original_alt_ratio - 1e-9, \
        f"alt_path_ratio decreased from {original_alt_ratio} to {bypass_alt_ratio}"
```

### Frontend Test Structure (Vitest)

```
frontend/src/__tests__/
â”œâ”€â”€ components/
â”‚   â”œâ”€â”€ DependencyMap.test.tsx        â† node click opens DetailsPanel (Req 14 AC 2a)
â”‚   â”œâ”€â”€ FilterToolbar.test.tsx        â† type filter hides nodes (Req 14 AC 2b)
â”‚   â”œâ”€â”€ SimulationIndicator.test.tsx  â† indicator appears on active sim (Req 14 AC 2c)
â”‚   â”œâ”€â”€ ResetButton.test.tsx          â† reset clears overlay (Req 14 AC 2d)
â”‚   â”œâ”€â”€ ApiErrorState.test.tsx        â† 500 shows error message (Req 14 AC 2e)
â”‚   â””â”€â”€ ScenarioSwitching.test.tsx    â† overlay clears on switch (Req 14 AC 2f)
â””â”€â”€ api/
    â””â”€â”€ client.test.ts                â† typed error handling
```

### How to Run Tests

```bash
# Backend (from /backend directory)
pytest tests/ -v

# Backend PBT only
pytest tests/test_impact_engine_pbt.py -v

# Frontend (from /frontend directory)
npx vitest --run
```

---

### Development Setup

#### Backend Setup (Windows, no Docker)

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**requirements.txt**:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
networkx==3.3
hypothesis==6.112.0
pytest==8.3.2
pytest-anyio==0.0.0
httpx==0.27.0
```

#### Frontend Setup

```bat
cd frontend
npm install
npm run dev
```

#### Environment Variables (backend/.env)

```
DATABASE_URL=sqlite:///./impactlens.db
CORS_ORIGIN=http://localhost:5173
```

The `CORS_ORIGIN` variable is read at startup; changing it requires a server restart (Req 9 AC 15).

#### Verification

After starting both servers:
- **Frontend**: http://localhost:5173 â€” should show the dark-themed dashboard with the "Database Failure" scenario auto-selected
- **API docs**: http://localhost:8000/docs â€” interactive OpenAPI documentation (Req 9 AC 10)
- **OpenAPI schema**: http://localhost:8000/openapi.json

#### DB Reset

To reset to seed data: delete `backend/impactlens.db` and restart the API server. The Seed_Loader will recreate and reseed on next startup (Req 10 AC 4).

---

### Scope Limitations

The following are explicitly **out of scope** for the initial version of ImpactLens:

| Feature | Rationale |
|---------|-----------|
| **Multi-step recovery** | The Recovery_Planner evaluates restoring only the direct simulation target. Combinations of multiple simultaneous restorations are not modelled. |
| **Capability-equivalence verification for alternative paths** | ImpactLens conservatively treats any non-failed inbound path as a valid alternative. Whether two paths provide equivalent capabilities (e.g., two databases with different data) requires engineer review and is always disclosed. |
| **Real AWS / cloud monitoring integration** | ImpactLens is an offline simulator. No AWS credentials, SDK, or live telemetry are required or supported. |
| **Authentication and user accounts** | No login screen, no RBAC, no sessions. The application is single-user by design. |
| **`component_degraded` reducing traversal** | When a component is degraded (not unavailable), its inbound and outbound edges remain traversable. Only the health overlay changes to "degraded". |
| **Deletion of Simulation_History records** | Records are retained indefinitely. No deletion endpoint is provided. |
| **Light theme** | Dark theme only in the initial version. Light theme is a stretch goal. |
| **Automatic dependency discovery** | All dependency data is entered manually or pre-loaded as seed data. There is no auto-discovery agent or cloud integration. |
| **Multi-worker / distributed deployment** | The Active Simulation store is in-memory and bound to a single process. Running multiple Uvicorn workers would produce inconsistent simulation state. Single-worker development mode is the supported configuration. |