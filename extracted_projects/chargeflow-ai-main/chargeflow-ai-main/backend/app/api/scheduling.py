"""
Scheduling API — POST /schedule
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.optimizer import schedule_charging

router = APIRouter()


class ScheduleRequest(BaseModel):
    ev_id: str = "EV001"
    station_id: str = "ST01"
    current_soc: int = 25
    target_soc: int = 90
    max_charge_rate_kw: int = 60


@router.post("/schedule")
def schedule(req: ScheduleRequest):
    from backend.app.api.stations import get_state

    state = get_state()

    ev = {
        "ev_id": req.ev_id,
        "current_soc": req.current_soc,
        "target_soc": req.target_soc,
        "max_charge_rate_kw": req.max_charge_rate_kw,
    }

    allocation = {
        "ev_id": req.ev_id,
        "station_id": req.station_id,
    }

    result = schedule_charging([ev], state.stations, [allocation])

    return result
