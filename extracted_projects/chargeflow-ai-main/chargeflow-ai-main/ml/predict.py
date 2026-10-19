"""
ChargeFlow AI — Demand Prediction Pipeline
============================================
Loads trained model, predicts demand/congestion for given station state.
"""

import os
import json
import joblib
import numpy as np
from datetime import datetime

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend", "station_num",
    "avg_energy", "avg_power", "avg_duration",
    "rolling_demand_3h", "rolling_demand_6h", "rolling_demand_12h",
    "demand_lag_1h", "demand_lag_24h",
    "is_morning_peak", "is_evening_peak",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
]

STATION_NUM_MAP = {"ST01": 0, "ST02": 1, "ST03": 2, "ST04": 3, "ST05": 4}

_model = None
_metrics = None


def _load_model():
    global _model, _metrics
    if _model is not None:
        return _model

    model_path = os.path.join(MODELS_DIR, "demand_model.pkl")
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. Run `python ml/train.py` first."
        )

    _model = joblib.load(model_path)

    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            _metrics = json.load(f)

    return _model


def predict_demand(
    station: dict,
    target_hour: int | None = None,
    target_dow: int | None = None,
) -> dict:
    """
    Predict demand for a station at a given hour.

    Returns predicted demand, utilisation, and congestion risk.
    """
    model = _load_model()

    now = datetime.now()
    hour = target_hour if target_hour is not None else now.hour
    dow = target_dow if target_dow is not None else now.weekday()
    is_weekend = 1 if dow >= 5 else 0

    station_num = STATION_NUM_MAP.get(station["station_id"], 0)

    # Derive features from station state
    current_util = station["current_load_kw"] / max(station["grid_limit_kw"], 1)
    avg_energy = current_util * 30  # Approximate
    avg_power = station["current_load_kw"] / max(station["total_chargers"], 1)
    avg_duration = 35  # Reasonable average

    # Approximate rolling demands from current queue + load
    base_demand = station["queue_length"] + (station["total_chargers"] - station["available_chargers"])
    rolling_3h = base_demand * 0.9
    rolling_6h = base_demand * 0.85
    rolling_12h = base_demand * 0.75
    demand_lag_1h = base_demand * 0.95
    demand_lag_24h = base_demand * 0.8

    is_morning_peak = 1 if 8 <= hour <= 10 else 0
    is_evening_peak = 1 if 17 <= hour <= 20 else 0
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    dow_sin = np.sin(2 * np.pi * dow / 7)
    dow_cos = np.cos(2 * np.pi * dow / 7)

    features = np.array([[
        hour, dow, is_weekend, station_num,
        avg_energy, avg_power, avg_duration,
        rolling_3h, rolling_6h, rolling_12h,
        demand_lag_1h, demand_lag_24h,
        is_morning_peak, is_evening_peak,
        hour_sin, hour_cos, dow_sin, dow_cos,
    ]])

    predicted_demand = max(0, float(model.predict(features)[0]))

    # Calculate utilisation and congestion risk
    predicted_utilisation = min(1.0, predicted_demand / max(station["total_chargers"], 1))
    congestion_risk = min(1.0, max(0.0, (predicted_utilisation - 0.5) / 0.5))

    return {
        "station_id": station["station_id"],
        "hour": hour,
        "day_of_week": dow,
        "predicted_demand": round(predicted_demand, 2),
        "predicted_utilisation": round(predicted_utilisation, 3),
        "congestion_risk": round(congestion_risk, 3),
        "current_utilisation": round(current_util, 3),
    }


def predict_multi_horizon(station: dict) -> dict:
    """
    Predict demand at 15, 30, 60, 120 minute horizons.
    """
    now = datetime.now()
    base_hour = now.hour
    base_dow = now.weekday()

    horizons = {}
    for offset_min, label in [(15, "15min"), (30, "30min"), (60, "60min"), (120, "120min")]:
        future_hour = (base_hour + offset_min // 60) % 24
        # DOW might change at midnight
        future_dow = base_dow if future_hour >= base_hour else (base_dow + 1) % 7
        pred = predict_demand(station, target_hour=future_hour, target_dow=future_dow)
        horizons[label] = pred

    return {
        "station_id": station["station_id"],
        "base_hour": base_hour,
        "horizons": horizons,
    }


def predict_all_stations(stations: list[dict]) -> dict[str, dict]:
    """Predict demand for all stations. Returns dict keyed by station_id."""
    results = {}
    for s in stations:
        try:
            pred = predict_demand(s)
            results[s["station_id"]] = pred
        except Exception as e:
            results[s["station_id"]] = {
                "station_id": s["station_id"],
                "predicted_demand": 0,
                "predicted_utilisation": 0,
                "congestion_risk": 0,
                "error": str(e),
            }
    return results


def get_model_metrics() -> dict | None:
    """Return saved model metrics."""
    _load_model()
    return _metrics
