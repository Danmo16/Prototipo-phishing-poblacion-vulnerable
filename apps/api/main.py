# apps/api/main.py
from fastapi import FastAPI

from apps.api.routes.health import router as health_router
from apps.api.routes.segments import router as segments_router
from apps.api.routes.templates import router as templates_router
from apps.api.routes.campaigns import router as campaigns_router
from apps.api.routes.targets import router as targets_router

app = FastAPI(
    title="Phishing Simulation Prototype (Academic)",
    version="0.1.0",
    description="API for managing simulated security-awareness campaigns (email MVP).",
)

app.include_router(health_router, tags=["health"])
app.include_router(segments_router, prefix="/segments", tags=["segments"])
app.include_router(templates_router, prefix="/templates", tags=["templates"])
app.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
app.include_router(targets_router, prefix="/targets", tags=["targets"])