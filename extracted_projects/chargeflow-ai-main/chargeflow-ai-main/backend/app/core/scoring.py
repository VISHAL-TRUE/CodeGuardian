"""
ChargeFlow AI — Multi-Factor Station Scoring
==============================================
Explainable weighted scoring for EV-station assignment.
Every score component is normalized to [0, 1] and transparent.
"""

import math
from typing import Any


DEFAULT_WEIGHTS = {
    "distance": 0.25,
    "availability": 0.25,
    "queue": 0.20,
    "grid_headroom": 0.20,
    "future_load": 0.10,
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def score_station(
    station: dict,
    ev: dict,
    predictions: dict | None = None,
    all_stations: list[dict] | None = None,
    weights: dict | None = None,
) -> dict:
    """
    Score a single station for a given EV request.

    Returns a dict with individual component scores, final weighted score,
    and human-readable breakdown.
    """
    w = weights or DEFAULT_WEIGHTS

    # --- Distance score ---
    dist_km = haversine_km(
        ev["latitude"], ev["longitude"],
        station["latitude"], station["longitude"],
    )
    # Normalize: closer is better. Max reasonable distance ~20 km.
    max_dist = 20.0
    distance_score = max(0.0, 1.0 - dist_km / max_dist)

    # --- Availability score ---
    avail_ratio = station["available_chargers"] / max(station["total_chargers"], 1)
    availability_score = avail_ratio  # Already [0, 1]

    # --- Queue score ---
    # Lower queue is better. Normalize by max_chargers * 2 as practical upper bound.
    max_queue = station["total_chargers"] * 2
    queue_score = max(0.0, 1.0 - station["queue_length"] / max(max_queue, 1))

    # --- Grid headroom score ---
    headroom = station["grid_limit_kw"] - station["current_load_kw"]
    headroom_ratio = headroom / max(station["grid_limit_kw"], 1)
    grid_headroom_score = max(0.0, min(1.0, headroom_ratio))

    # --- Future load score (predicted availability) ---
    future_load_score = 0.5  # Default neutral
    if predictions and station["station_id"] in predictions:
        pred = predictions[station["station_id"]]
        # Lower predicted demand → better
        if "predicted_utilisation" in pred:
            future_load_score = max(0.0, 1.0 - pred["predicted_utilisation"])
        elif "congestion_risk" in pred:
            future_load_score = max(0.0, 1.0 - pred["congestion_risk"])

    # --- Weighted final score ---
    final_score = (
        w["distance"] * distance_score +
        w["availability"] * availability_score +
        w["queue"] * queue_score +
        w["grid_headroom"] * grid_headroom_score +
        w["future_load"] * future_load_score
    )

    return {
        "station_id": station["station_id"],
        "station_name": station["name"],
        "distance_km": round(dist_km, 2),
        "scores": {
            "distance": round(distance_score, 3),
            "availability": round(availability_score, 3),
            "queue": round(queue_score, 3),
            "grid_headroom": round(grid_headroom_score, 3),
            "future_load": round(future_load_score, 3),
        },
        "weights": w,
        "final_score": round(final_score, 3),
    }


def rank_stations(
    stations: list[dict],
    ev: dict,
    predictions: dict | None = None,
    weights: dict | None = None,
) -> list[dict]:
    """
    Score and rank all stations for a given EV.
    Returns list sorted by final_score descending.
    """
    scored = [
        score_station(s, ev, predictions, stations, weights)
        for s in stations
    ]
    scored.sort(key=lambda x: x["final_score"], reverse=True)

    # Mark recommended
    for i, s in enumerate(scored):
        s["rank"] = i + 1
        s["recommended"] = i == 0

    return scored
