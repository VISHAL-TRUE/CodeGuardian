"""
ChargeFlow AI — Deterministic Synthetic Data Generator
=======================================================
Generates stations.csv, charging_sessions.csv, and ev_requests.csv
with fixed random seed for reproducible demo scenarios.
"""

import csv
import os
import random
import math
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Stations — 5 stations in a realistic metro-area cluster (Chennai region)
# ---------------------------------------------------------------------------
STATIONS = [
    {
        "station_id": "ST01",
        "name": "Central Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "total_chargers": 8,
        "available_chargers": 3,
        "max_power_kw": 480.0,
        "current_load_kw": 310.0,
        "grid_limit_kw": 500.0,
        "queue_length": 4,
        "price_per_kwh": 16.0,
    },
    {
        "station_id": "ST02",
        "name": "Anna Nagar",
        "latitude": 13.0850,
        "longitude": 80.2101,
        "total_chargers": 6,
        "available_chargers": 4,
        "max_power_kw": 360.0,
        "current_load_kw": 120.0,
        "grid_limit_kw": 400.0,
        "queue_length": 1,
        "price_per_kwh": 16.0,
    },
    {
        "station_id": "ST03",
        "name": "T. Nagar",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "total_chargers": 5,
        "available_chargers": 2,
        "max_power_kw": 300.0,
        "current_load_kw": 200.0,
        "grid_limit_kw": 350.0,
        "queue_length": 3,
        "price_per_kwh": 16.0,
    },
    {
        "station_id": "ST04",
        "name": "Adyar",
        "latitude": 13.0067,
        "longitude": 80.2570,
        "total_chargers": 10,
        "available_chargers": 7,
        "max_power_kw": 600.0,
        "current_load_kw": 180.0,
        "grid_limit_kw": 650.0,
        "queue_length": 0,
        "price_per_kwh": 16.0,
    },
    {
        "station_id": "ST05",
        "name": "OMR / Perungudi",
        "latitude": 12.9650,
        "longitude": 80.2460,
        "total_chargers": 7,
        "available_chargers": 5,
        "max_power_kw": 420.0,
        "current_load_kw": 150.0,
        "grid_limit_kw": 450.0,
        "queue_length": 1,
        "price_per_kwh": 16.0,
    },
]


def write_stations():
    path = os.path.join(DATA_DIR, "stations.csv")
    fieldnames = list(STATIONS[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(STATIONS)
    print(f"  ✓ stations.csv — {len(STATIONS)} stations")


# ---------------------------------------------------------------------------
# Charging Sessions — ~3000 historical sessions over 30 days
# ---------------------------------------------------------------------------

def _demand_multiplier(hour: int, is_weekend: bool) -> float:
    """Realistic bi-modal demand: morning peak 8-10, evening peak 17-20."""
    if is_weekend:
        if 10 <= hour <= 14:
            return 1.4
        if 15 <= hour <= 19:
            return 1.2
        return 0.6
    # Weekday
    if 8 <= hour <= 10:
        return 1.6
    if 17 <= hour <= 20:
        return 1.8
    if 11 <= hour <= 16:
        return 1.0
    return 0.4


def write_charging_sessions():
    path = os.path.join(DATA_DIR, "charging_sessions.csv")
    fieldnames = [
        "session_id", "station_id", "timestamp", "arrival_hour",
        "day_of_week", "battery_soc", "target_soc", "energy_requested_kwh",
        "charging_power_kw", "charging_duration_min",
    ]
    sessions = []
    sid = 1
    base_date = datetime(2026, 7, 1)

    for day_offset in range(30):
        dt = base_date + timedelta(days=day_offset)
        is_weekend = dt.weekday() >= 5
        for hour in range(24):
            mult = _demand_multiplier(hour, is_weekend)
            # Each station gets a probabilistic number of sessions per hour
            for st in STATIONS:
                n_sessions = int(mult * (st["total_chargers"] / 3.0) + random.random())
                for _ in range(n_sessions):
                    minute = random.randint(0, 59)
                    ts = dt.replace(hour=hour, minute=minute, second=0)
                    soc = random.randint(10, 50)
                    target = random.randint(max(soc + 20, 70), 100)
                    energy = round((target - soc) / 100.0 * random.uniform(40, 75), 1)
                    power = random.choice([22, 50, 60, 120, 150])
                    duration = round(energy / power * 60, 1)
                    sessions.append({
                        "session_id": f"S{sid:05d}",
                        "station_id": st["station_id"],
                        "timestamp": ts.isoformat(),
                        "arrival_hour": hour,
                        "day_of_week": dt.weekday(),
                        "battery_soc": soc,
                        "target_soc": target,
                        "energy_requested_kwh": energy,
                        "charging_power_kw": power,
                        "charging_duration_min": duration,
                    })
                    sid += 1

    random.shuffle(sessions)
    # Re-sort by timestamp for cleanliness
    sessions.sort(key=lambda x: x["timestamp"])

    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(sessions)
    print(f"  ✓ charging_sessions.csv — {len(sessions)} sessions")


# ---------------------------------------------------------------------------
# EV Requests — incoming EVs for the simulation
# ---------------------------------------------------------------------------

def write_ev_requests():
    path = os.path.join(DATA_DIR, "ev_requests.csv")
    fieldnames = [
        "ev_id", "current_soc", "target_soc", "max_charge_rate_kw",
        "arrival_time", "deadline", "latitude", "longitude",
    ]
    requests = []
    base_time = datetime(2026, 8, 19, 8, 0, 0)  # Demo day morning

    for i in range(1, 21):
        soc = random.randint(8, 40)
        target = random.randint(max(soc + 30, 75), 100)
        rate = random.choice([22, 50, 60, 120, 150])
        arrival = base_time + timedelta(minutes=random.randint(0, 180))
        # Deadline = arrival + 30-120 min
        deadline = arrival + timedelta(minutes=random.randint(30, 120))
        # Random location near the station cluster (Chennai region)
        lat = 13.05 + random.uniform(-0.06, 0.06)
        lon = 80.25 + random.uniform(-0.04, 0.04)
        requests.append({
            "ev_id": f"EV{i:03d}",
            "current_soc": soc,
            "target_soc": target,
            "max_charge_rate_kw": rate,
            "arrival_time": arrival.isoformat(),
            "deadline": deadline.isoformat(),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        })

    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(requests)
    print(f"  ✓ ev_requests.csv — {len(requests)} EV requests")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("ChargeFlow AI — Generating synthetic data …")
    ensure_dir()
    write_stations()
    write_charging_sessions()
    write_ev_requests()
    print("Done ✓")


if __name__ == "__main__":
    main()
