"""
Forecasting API — POST /forecast
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ForecastRequest(BaseModel):
    station_id: str | None = None
    hour: int | None = None
    day_of_week: int | None = None


@router.post("/forecast")
def forecast(req: ForecastRequest):
    from backend.app.api.stations import get_state

    state = get_state()

    try:
        from ml.predict import predict_demand, predict_multi_horizon, predict_all_stations, get_model_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model not available: {str(e)}")

    if req.station_id:
        station = state.get_station(req.station_id)
        if not station:
            raise HTTPException(status_code=404, detail=f"Station {req.station_id} not found")

        prediction = predict_demand(station, req.hour, req.day_of_week)
        multi = predict_multi_horizon(station)
        return {
            "prediction": prediction,
            "multi_horizon": multi,
            "model_metrics": get_model_metrics(),
        }
    else:
        # Predict for all stations
        predictions = predict_all_stations(state.stations)
        state.predictions = predictions  # Update simulation state
        return {
            "predictions": predictions,
            "model_metrics": get_model_metrics(),
        }
