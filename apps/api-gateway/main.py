"""Aegis / Meridian Central API Gateway Application."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from services.accounts_ledger.api import router as ledger_router
from services.common.config import settings
from services.common.db import init_db
from services.common.telemetry import metrics
from services.identity.api import router as auth_router
from services.payments.api import router as payments_router
from agent_platform.gateway.api import router as approvals_router
from agent_platform.gateway.admin_api import router as admin_router
from agent_platform.gateway.mcp_server import router as mcp_router
from agent_platform.squads.onboarding.api import router as onboarding_router
from agent_platform.squads.aegis.api import router as aegis_router
from agent_platform.squads.reconciliation.api import router as reconciliation_router
from agent_platform.squads.support_disputes.api import router as disputes_router
from agent_platform.squads.ops_copilot.api import router as copilot_router
import agent_platform.gateway.tools  # Register tools in gateway registry
import agent_platform.squads.onboarding.tools  # Register onboarding tools in gateway registry
import agent_platform.squads.aegis.tools  # Register Aegis AML tools in gateway registry
import agent_platform.squads.reconciliation.tools  # Register B2B reconciliation tools in gateway registry
import agent_platform.squads.support_disputes.tools  # Register Support & Disputes tools in gateway registry
import agent_platform.squads.ops_copilot.tools  # Register Ops Copilot tools in gateway registry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and teardown lifespan events."""
    print("🚀 Initializing Aegis / Meridian Platform...")
    # Initialize database tables if running in development mode
    if settings.ENVIRONMENT == "development":
        try:
            await init_db()
            print(" Database tables initialized.")
        except Exception as e:
            print(f"⚠️ Notice: Database initialization skipped or deferred: {e}")
    yield
    print(" Shutting down Aegis / Meridian Platform...")


app = FastAPI(
    title="Aegis / Meridian API Gateway",
    version="0.1.0",
    description="Agentic Payments and Simulated Banking Platform powered by Google Gemini 3.8 Flash and agy",
    lifespan=lifespan,
)

# CORS Configuration for Customer Portal & Operations Console
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Customer Portal
        "http://localhost:3001",  # Operations Console
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ledger_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(aegis_router, prefix="/api/v1")
app.include_router(reconciliation_router, prefix="/api/v1")
app.include_router(disputes_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api/v1")


@app.get("/", tags=["Root"], summary="API Gateway Index")
async def root() -> Dict[str, Any]:
    """Root entrypoint providing service status and API documentation links."""
    return {
        "service": "Aegis / Meridian Central API Gateway",
        "status": "ONLINE",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_check": "/api/v1/health",
        "metrics": "/metrics",
        "version": "0.1.0",
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Readiness and liveness probe endpoint."""
    return {
        "status": "HEALTHY",
        "service": "aegis-api-gateway",
        "environment": settings.ENVIRONMENT,
        "gemini_model": settings.GEMINI_MODEL,
    }


@app.get("/metrics", tags=["Telemetry"], summary="Prometheus scraping metrics endpoint")
async def prometheus_metrics() -> Response:
    """Export platform metrics in Prometheus text format."""
    return Response(content=metrics.export_prometheus_text(), media_type="text/plain; version=0.0.4")
