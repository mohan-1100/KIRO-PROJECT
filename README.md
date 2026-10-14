# ImpactLens

**Explainable Network Dependency and Outage Impact Simulator**

ImpactLens is a web-based tool for visualising infrastructure dependency graphs, simulating component failures, and explaining exactly why each downstream service is affected — using traceable dependency chains and a transparent impact scoring formula.

> All infrastructure data in this application is **simulated**. No real AWS credentials, cloud accounts, or production systems are required or accessed.

---

## Prerequisites

- Python 3.11 or later
- Node.js 20 or later
- Windows (PowerShell or Command Prompt)

---

## Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env` (already included) — defaults are:
```
DATABASE_URL=sqlite:///./impactlens.db
CORS_ORIGIN=http://localhost:5173
```

Start the API server:
```powershell
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

---

## Verification

| What | URL |
|------|-----|
| Frontend application | http://localhost:5173 |
| API interactive docs | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |

---

## Demo Scenarios

ImpactLens ships with four pre-loaded demonstration scenarios:

| Scenario | What it demonstrates |
|----------|---------------------|
| Database Failure | Primary database outage cascading to API services and the web app |
| Shared Dependency Failure | Auth service failure affecting multiple consumers simultaneously |
| Alternative Path Available | A failure where one service has a redundant route and is reported separately |
| Incomplete Evidence | Stale dependency data triggering data quality warnings in the impact report |

---

## Running Tests

**Backend tests** (from the `backend/` directory with venv active):
```powershell
pytest tests/ -v
```

**Frontend tests** (from the `frontend/` directory):
```powershell
npx vitest --run
```

---

## Database Reset

To reset all data and reload the demo scenarios:

1. Stop the API server.
2. Delete `backend/impactlens.db`.
3. Restart the API server — the database is recreated and seeded automatically.

---

## Project Structure

```
KIRO-PROJECT/
├── backend/          # FastAPI + NetworkX + SQLite
│   ├── app/
│   │   ├── routers/      # API endpoint handlers
│   │   ├── models/       # Pydantic request/response models
│   │   ├── db/           # SQLite connection and CRUD helpers
│   │   ├── engine/       # Graph traversal, impact scoring, recovery analysis
│   │   └── seed/         # Demo data fixtures and seed loader
│   └── tests/            # Pytest unit and API tests
└── frontend/         # React + Vite + TypeScript + Tailwind + React Flow
    └── src/
        ├── api/          # Typed API client modules
        ├── contexts/     # ScenarioContext, SimulationContext
        ├── pages/        # One file per page (8 pages)
        └── components/   # Shared UI components
```

---

## Architecture

- **Edge convention**: `A → B` means B depends on A. If A fails, B may be affected.
- **Impact Score**: A heuristic (0–100) combining criticality, downstream reach, dependency distance, and isolation. Labelled "ImpactLens heuristic v1.0 — not an industry standard metric".
- **Alternative paths**: When a service has an apparent inbound route from a non-failed source, ImpactLens records it as a **possible alternative** and keeps the service in the affected set. Operational equivalence must be verified by an engineer.
- **Active simulations**: Stored in server memory only. Lost on server restart. Simulation history is persisted to SQLite.

---

## Known Limitations

- No real AWS, GCP, or Azure monitoring integration.
- No authentication or user accounts.
- No multi-step recovery analysis (single target restoration only).
- Alternative path detection is topology-only — capability equivalence is not verified.
- Active simulation state is lost on server restart; simulation history is preserved.
- Light theme is not implemented in the initial version.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Flow, Recharts, Lucide React |
| Backend | Python 3.11, FastAPI, Pydantic v2, NetworkX, SQLite |
| Testing | Pytest, Hypothesis (PBT), Vitest, React Testing Library |
