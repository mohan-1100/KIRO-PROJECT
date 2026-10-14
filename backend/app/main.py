"""
ImpactLens FastAPI application entry point.

Startup sequence:
  1. Create all SQLite tables (idempotent — safe on every restart)
  2. Run Seed_Loader if the DB is empty (inserts demo data)
  3. Accept requests

CORS is configured to allow the Vite frontend (default: http://localhost:5173).
Override via the CORS_ORIGIN environment variable.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db.schema import create_tables
from app.models.common import ProblemDetail

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before accepting requests."""
    create_tables()

    # Lazy import to avoid circular deps; seed only runs if DB is empty
    from app.seed.seed_loader import run_seed_if_needed
    run_seed_if_needed()

    yield  # Application runs here


app = FastAPI(
    title="ImpactLens API",
    version="1.0.0",
    description=(
        "Explainable Network Dependency and Outage Impact Simulator. "
        "All infrastructure data is simulated — no real AWS credentials required."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global error handler — returns RFC 7807 Problem Detail JSON for all errors
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ProblemDetail(
                type=f"https://impactlens.local/errors/http-{exc.status_code}",
                title=exc.detail if isinstance(exc.detail, str) else "Request error",
                status=exc.status_code,
                detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                instance=str(request.url.path),
            ).model_dump(),
        )
    return JSONResponse(
        status_code=500,
        content=ProblemDetail(
            type="https://impactlens.local/errors/internal-server-error",
            title="Internal Server Error",
            status=500,
            detail=str(exc),
            instance=str(request.url.path),
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "ImpactLens API", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from app.routers import scenarios, components, edges, incidents, settings as settings_router
from app.routers import data_quality as data_quality_router
from app.routers import simulations as simulations_router

app.include_router(scenarios.router)
app.include_router(components.router)
app.include_router(edges.router)
app.include_router(incidents.router)
app.include_router(settings_router.router)
app.include_router(data_quality_router.router)
app.include_router(simulations_router.router)
