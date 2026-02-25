"""FastAPI application — mounts routes, serves built frontend."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.routers import health_router, crew_router

app = FastAPI(title="Akamai Edge AI Market Analyst")

# API routes
app.include_router(health_router.router, prefix="/api")
app.include_router(crew_router.router, prefix="/api/crew")

# WebSocket routes (separate prefix from REST)
app.include_router(crew_router.ws_router, prefix="/ws/crew")

# Serve chart images from output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# Serve built Svelte frontend (production)
frontend_build = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build.exists() and (frontend_build / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
