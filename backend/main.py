"""
VPP Trading Terminal - FastAPI Backend
========================================
Main entry point for the optional FastAPI backend. Mounts the VPP
optimization routes and the solar forecasting routes.

Run locally with:
    cd backend
    uvicorn main:app --reload --port 8000
"""

# AI-assisted (Claude, 9308ab3): this file was written with Claude (it was missing
# but imported by the integration tests).

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import vpp, solar

app = FastAPI(
    title="VPP Trading Terminal API",
    description="Backend API for Virtual Power Plant optimization and solar forecasting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vpp.router, prefix="/vpp", tags=["VPP"])
app.include_router(solar.router, prefix="/solar", tags=["Solar"])


@app.get("/")
def root():
    """Basic health check for the API."""
    return {
        "status": "operational",
        "service": "VPP Trading Terminal API",
        "version": "1.0.0",
    }
