"""
ChargeFlow AI — Simulation Engine
===================================
Manages simulation state, peak demand injection, and baseline comparison.
All metrics are calculated, never hardcoded.
"""

import copy
import csv
import json
import math
import os
import random
from datetime import datetime, timedelta
from typing import Any

SEED = 42
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios")


def _load_stations() -> list[dict]:
    path = os.path.join(DATA_DIR, "stations.csv")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append({
                "station_id": r["station_id"],
                "name": r["name"],
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "total_chargers": int(r["total_chargers"]),
                "available_chargers": int(r["available_chargers"]),
                "max_power_kw": float(r["max_power_kw"]),
                "current_load_kw": float(r["current_load_kw"]),
                "grid_limit_kw": float(r["grid_limit_kw"]),
                "queue_length": int(r["queue_length"]),
                "price_per_kwh": float(r["price_per_kwh"]),
            })
        return rows


def _load_ev_requests() -> list[dict]:
    path = os.path.join(DATA_DIR, "ev_requests.csv")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "ev_id": r["ev_id"],
                "current_soc": int(r["current_soc"]),
                "target_soc": int(r["target_soc"]),
                "max_charge_rate_kw": int(r["max_charge_rate_kw"]),
                "arrival_time": r["arrival_time"],
                "deadline": r["deadline"],
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
            }
            for r in reader
        ]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class SimulationState:
    """Holds live mutable state for the simulation."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.stations = _load_stations()
        self.ev_requests = _load_ev_requests()
        self.pending_evs: list[dict] = []
        self.allocated_evs: list[dict] = []
        self.baseline_metrics: dict | None = None
        self.optimised_metrics: dict | None = None
        self.scenario = "normal"
        self.congestion_alerts: list[str] = []
        self.is_peak = False
        self.is_optimised = False
        self.predictions: dict[str, dict] = {}  # station_id -> prediction

    def get_station(self, station_id: str) -> dict | None:
        for s in self.stations:
            if s["station_id"] == station_id:
                return s
        return None

    def inject_peak_demand(self):
        """Simulate a peak demand burst targeting ST01."""
        random.seed(SEED + 1)
        self.scenario = "peak"
        self.is_peak = True
        self.is_optimised = False
        self.optimised_metrics = None

        # Reset allocated
        self.allocated_evs = []

        # Overload ST01
        st01 = self.get_station("ST01")
        if st01:
            st01["current_load_kw"] = st01["grid_limit_kw"] * 0.95  # Near grid limit
            st01["available_chargers"] = 1
            st01["queue_length"] = 8

        # Moderate load on ST03
        st03 = self.get_station("ST03")
        if st03:
            st03["current_load_kw"] = st03["grid_limit_kw"] * 0.78
            st03["available_chargers"] = 1
            st03["queue_length"] = 5

        # Generate burst EVs — 12 EVs near ST01
        burst_evs = []
        base_time = datetime(2026, 8, 19, 17, 30, 0)  # Evening peak
        for i in range(12):
            soc = random.randint(10, 35)
            target = random.randint(80, 100)
            rate = random.choice([50, 60, 120, 150])
            arrival = base_time + timedelta(minutes=random.randint(0, 30))
            deadline = arrival + timedelta(minutes=random.randint(40, 90))
            # Cluster near ST01 (Central Chennai)
            lat = 13.0827 + random.uniform(-0.008, 0.008)
            lon = 80.2707 + random.uniform(-0.008, 0.008)
            burst_evs.append({
                "ev_id": f"BURST{i + 1:03d}",
                "current_soc": soc,
                "target_soc": target,
                "max_charge_rate_kw": rate,
                "arrival_time": arrival.isoformat(),
                "deadline": deadline.isoformat(),
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
            })

        self.pending_evs = burst_evs

        # Build congestion alerts
        self.congestion_alerts = []
        for s in self.stations:
            util = s["current_load_kw"] / s["grid_limit_kw"]
            if util > 0.85:
                self.congestion_alerts.append(
                    f"⚠ {s['name']} ({s['station_id']}): Load at {util * 100:.0f}% of grid limit — CONGESTION RISK"
                )
            elif util > 0.65:
                self.congestion_alerts.append(
                    f"⚡ {s['name']} ({s['station_id']}): Load at {util * 100:.0f}% — Elevated demand"
                )

        # Calculate baseline metrics (nearest-station naive)
        self.baseline_metrics = self._run_baseline(burst_evs)

    def inject_grid_constraint(self):
        """Simulate grid constraint — tighter limits at ST01 and ST03."""
        self.inject_peak_demand()
        self.scenario = "grid_constraint"

        st01 = self.get_station("ST01")
        if st01:
            st01["grid_limit_kw"] = 400  # Reduced from 500

        st03 = self.get_station("ST03")
        if st03:
            st03["grid_limit_kw"] = 280  # Reduced from 350

        # Recalculate baseline
        self.baseline_metrics = self._run_baseline(self.pending_evs)

        self.congestion_alerts.append(
            "🔴 Grid constraint active: Transformer limits reduced at ST01 and ST03"
        )

    def _run_baseline(self, evs: list[dict]) -> dict:
        """Nearest-station baseline: each EV goes to nearest available station."""
        sim_stations = copy.deepcopy(self.stations)
        total_wait = 0.0
        total_queue = 0
        grid_overloads = 0
        assignments = []

        for ev in evs:
            # Find nearest station with any capacity
            best = None
            best_dist = float("inf")
            for s in sim_stations:
                d = haversine_km(ev["latitude"], ev["longitude"],
                                 s["latitude"], s["longitude"])
                if d < best_dist:
                    best_dist = d
                    best = s

            if best is None:
                continue

            # Assign EV
            energy = (ev["target_soc"] - ev["current_soc"]) / 100.0 * 60  # ~60 kWh battery
            power = min(ev["max_charge_rate_kw"], 60)  # Assume 60 kW average
            duration = energy / power * 60  # minutes

            # Update station state
            best["current_load_kw"] += power
            best["queue_length"] += 1
            if best["available_chargers"] > 0:
                best["available_chargers"] -= 1

            wait = max(0, best["queue_length"] - best["total_chargers"]) * 15  # 15 min per queue position
            total_wait += wait
            total_queue += best["queue_length"]

            if best["current_load_kw"] > best["grid_limit_kw"]:
                grid_overloads += 1

            assignments.append({
                "ev_id": ev["ev_id"],
                "station_id": best["station_id"],
                "distance_km": round(best_dist, 2),
                "wait_min": round(wait, 1),
            })

        n = len(evs) if evs else 1
        station_loads = [s["current_load_kw"] / s["grid_limit_kw"] for s in sim_stations]
        load_imbalance = max(station_loads) - min(station_loads) if station_loads else 0

        return {
            "strategy": "Uncoordinated Baseline",
            "avg_wait_min": round(total_wait / n, 1),
            "avg_queue_length": round(total_queue / n, 1),
            "peak_grid_utilisation": round(max(station_loads) * 100, 1),
            "grid_overload_events": grid_overloads,
            "load_imbalance": round(load_imbalance * 100, 1),
            "total_evs": len(evs),
            "assignments": assignments,
            "station_states": [
                {
                    "station_id": s["station_id"],
                    "current_load_kw": round(s["current_load_kw"], 1),
                    "grid_limit_kw": s["grid_limit_kw"],
                    "utilisation_pct": round(s["current_load_kw"] / s["grid_limit_kw"] * 100, 1),
                    "queue_length": s["queue_length"],
                    "available_chargers": s["available_chargers"],
                }
                for s in sim_stations
            ],
        }

    def to_dict(self) -> dict:
        """Serialize current state for API response."""
        return {
            "scenario": self.scenario,
            "is_peak": self.is_peak,
            "is_optimised": self.is_optimised,
            "stations": self.stations,
            "pending_evs": len(self.pending_evs),
            "allocated_evs": len(self.allocated_evs),
            "congestion_alerts": self.congestion_alerts,
            "baseline_metrics": self.baseline_metrics,
            "optimised_metrics": self.optimised_metrics,
            "predictions": self.predictions,
        }
