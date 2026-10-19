"""
Allocation API — POST /allocate
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.scoring import rank_stations
from backend.app.core.pricing import calculate_all_prices

router = APIRouter()


class AllocateRequest(BaseModel):
    ev_id: str = "DRIVER01"
    current_soc: int = 25
    target_soc: int = 90
    max_charge_rate_kw: int = 60
    latitude: float = 13.060
    longitude: float = 80.260
    deadline: str | None = None


@router.post("/allocate")
def allocate(req: AllocateRequest):
    from backend.app.api.stations import get_state

    state = get_state()

    ev = {
        "ev_id": req.ev_id,
        "current_soc": req.current_soc,
        "target_soc": req.target_soc,
        "max_charge_rate_kw": req.max_charge_rate_kw,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "deadline": req.deadline,
    }

    # Score and rank all stations
    rankings = rank_stations(state.stations, ev, state.predictions)

    # Attach pricing
    prices = calculate_all_prices(state.stations, state.predictions)
    price_map = {p["station_id"]: p for p in prices}

    for r in rankings:
        r["pricing"] = price_map.get(r["station_id"], {})

    recommended = rankings[0] if rankings else None
    alternatives = rankings[1:] if len(rankings) > 1 else []

    return {
        "ev_id": req.ev_id,
        "recommended": recommended,
        "alternatives": alternatives,
        "total_stations_evaluated": len(rankings),
    }
