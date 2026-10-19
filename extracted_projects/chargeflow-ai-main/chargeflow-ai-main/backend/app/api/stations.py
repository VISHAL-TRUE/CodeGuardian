"""
Stations API — GET /stations, GET /stations/{id}
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter, HTTPException

from simulation.simulator import SimulationState
from backend.app.core.pricing import calculate_all_prices

router = APIRouter()

# Shared simulation state (singleton)
_state: SimulationState | None = None


def get_state() -> SimulationState:
    global _state
    if _state is None:
        _state = SimulationState()
    return _state


@router.get("/stations")
def list_stations():
    state = get_state()
    prices = calculate_all_prices(state.stations, state.predictions)
    price_map = {p["station_id"]: p for p in prices}

    stations_out = []
    for s in state.stations:
        util = s["current_load_kw"] / max(s["grid_limit_kw"], 1)
        status = "green" if util < 0.5 else ("yellow" if util < 0.8 else "red")
        pred = state.predictions.get(s["station_id"], {})

        stations_out.append({
            **s,
            "utilisation_pct": round(util * 100, 1),
            "status": status,
            "pricing": price_map.get(s["station_id"], {}),
            "prediction": pred,
        })

    return {
        "stations": stations_out,
        "scenario": state.scenario,
        "is_peak": state.is_peak,
        "is_optimised": state.is_optimised,
    }


@router.get("/stations/{station_id}")
def get_station(station_id: str):
    state = get_state()
    s = state.get_station(station_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    util = s["current_load_kw"] / max(s["grid_limit_kw"], 1)
    status = "green" if util < 0.5 else ("yellow" if util < 0.8 else "red")
    pred = state.predictions.get(station_id, {})

    prices = calculate_all_prices([s], state.predictions)

    return {
        **s,
        "utilisation_pct": round(util * 100, 1),
        "status": status,
        "pricing": prices[0] if prices else {},
        "prediction": pred,
    }
