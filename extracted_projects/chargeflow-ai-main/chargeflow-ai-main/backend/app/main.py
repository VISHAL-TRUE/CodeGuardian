"""
ChargeFlow AI — FastAPI Backend
================================
Main application with CORS, modular routing, and health checks.
"""

import os
import sys

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import stations, forecasting, allocation, scheduling, simulation

app = FastAPI(
    title="ChargeFlow AI",
    description="Predictive & Grid-Aware EV Charging Optimisation",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(stations.router, prefix="/api", tags=["Stations"])
app.include_router(forecasting.router, prefix="/api", tags=["Forecasting"])
app.include_router(allocation.router, prefix="/api", tags=["Allocation"])
app.include_router(scheduling.router, prefix="/api", tags=["Scheduling"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])


@app.get("/")
def root():
    return {
        "name": "ChargeFlow AI",
        "tagline": "Predictive & Grid-Aware EV Charging Optimisation",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
