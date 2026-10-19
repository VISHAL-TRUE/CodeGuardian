"""
Simulation API — POST /simulate/peak, POST /simulate/reset, POST /simulate/optimize,
                  GET /simulation/state, GET /metrics
"""

import copy
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter

from backend.app.core.scoring import rank_stations
from backend.app.core.optimizer import schedule_charging
from backend.app.core.pricing import calculate_all_prices

router = APIRouter()


@router.post("/simulate/peak")
def simulate_peak():
    from backend.app.api.stations import get_state

    state = get_state()
    state.inject_peak_demand()

    # Run predictions if model available
    try:
        from ml.predict import predict_all_stations
        state.predictions = predict_all_stations(state.stations)
    except Exception:
        pass

    prices = calculate_all_prices(state.stations, state.predictions)

    return {
        "message": "Peak demand injected. 12 EVs burst near Central Chennai (ST01).",
        "scenario": state.scenario,
        "pending_evs": len(state.pending_evs),
        "congestion_alerts": state.congestion_alerts,
        "baseline_metrics": state.baseline_metrics,
        "stations": state.stations,
        "prices": prices,
        "predictions": state.predictions,
    }


@router.post("/simulate/grid-constraint")
def simulate_grid_constraint():
    from backend.app.api.stations import get_state

    state = get_state()
    state.inject_grid_constraint()

    try:
        from ml.predict import predict_all_stations
        state.predictions = predict_all_stations(state.stations)
    except Exception:
        pass

    prices = calculate_all_prices(state.stations, state.predictions)

    return {
        "message": "Grid constraint active. Transformer limits reduced at ST01 and ST03.",
        "scenario": state.scenario,
        "pending_evs": len(state.pending_evs),
        "congestion_alerts": state.congestion_alerts,
        "baseline_metrics": state.baseline_metrics,
        "stations": state.stations,
        "prices": prices,
        "predictions": state.predictions,
    }


@router.post("/simulate/optimize")
def simulate_optimize():
    from backend.app.api.stations import get_state

    state = get_state()

    if not state.pending_evs:
        return {
            "message": "No pending EVs to optimize. Run peak simulation first.",
            "optimised_metrics": None,
        }

    # Step 1: Allocate each pending EV using scoring
    allocations = []
    all_rankings = []

    # Work on a copy of stations to track cumulative changes
    working_stations = copy.deepcopy(state.stations)

    for ev in state.pending_evs:
        rankings = rank_stations(working_stations, ev, state.predictions)
        best = rankings[0]

        allocations.append({
            "ev_id": ev["ev_id"],
            "station_id": best["station_id"],
            "score": best["final_score"],
            "scores": best["scores"],
            "distance_km": best["distance_km"],
        })

        # Update working station state to reflect this allocation
        for ws in working_stations:
            if ws["station_id"] == best["station_id"]:
                ws["queue_length"] += 1
                ws["current_load_kw"] += min(ev["max_charge_rate_kw"], 60)
                if ws["available_chargers"] > 0:
                    ws["available_chargers"] -= 1
                break

        all_rankings.append({
            "ev_id": ev["ev_id"],
            "rankings": rankings,
        })

    # Step 2: Schedule charging with PuLP
    schedule_result = schedule_charging(state.pending_evs, state.stations, allocations)

    # Step 3: Validate solver status and apply PuLP-scheduled power values
    feasibility_issues = schedule_result.get("feasibility_issues", [])
    pulp_schedules = schedule_result.get("schedules", [])

    # Aggregate PuLP results by station, distinguishing active vs deferred
    station_active_power = {}   # station_id -> total kW from active EVs
    station_active_count = {}   # station_id -> number of actively charging EVs
    station_deferred_count = {} # station_id -> number of deferred/waiting EVs

    for sched in pulp_schedules:
        sid = sched["station_id"]
        if sched.get("is_active", False):
            station_active_power[sid] = station_active_power.get(sid, 0) + sched["charging_power_kw"]
            station_active_count[sid] = station_active_count.get(sid, 0) + 1
        else:
            station_deferred_count[sid] = station_deferred_count.get(sid, 0) + 1

    for s in state.stations:
        sid = s["station_id"]
        active_power = station_active_power.get(sid, 0)
        active_count = station_active_count.get(sid, 0)
        deferred_count = station_deferred_count.get(sid, 0)

        # Apply PuLP-scheduled power directly (already grid-constrained by solver)
        s["current_load_kw"] = round(s["current_load_kw"] + active_power, 1)
        # Only deferred EVs join the queue; active EVs occupy chargers
        s["queue_length"] += deferred_count
        s["available_chargers"] = max(0, s["available_chargers"] - active_count)

    # Step 4: Calculate optimised metrics
    total_wait = 0
    total_queue = 0
    grid_overloads = 0

    for s in state.stations:
        excess_queue = max(0, s["queue_length"] - s["total_chargers"])
        total_queue += s["queue_length"]
        total_wait += excess_queue * 12  # ~12 min per queue position

        if s["current_load_kw"] > s["grid_limit_kw"]:
            grid_overloads += 1

    n = len(state.pending_evs)
    station_loads = [s["current_load_kw"] / s["grid_limit_kw"] for s in state.stations]
    load_imbalance = max(station_loads) - min(station_loads) if station_loads else 0

    optimised_metrics = {
        "strategy": "ChargeFlow AI",
        "avg_wait_min": round(total_wait / n, 1),
        "avg_queue_length": round(total_queue / len(state.stations), 1),
        "peak_grid_utilisation": round(max(station_loads) * 100, 1),
        "grid_overload_events": grid_overloads,
        "load_imbalance": round(load_imbalance * 100, 1),
        "total_evs": n,
        "schedule_summary": {
            "active_evs": schedule_result.get("active_evs", 0),
            "delayed_evs": schedule_result.get("delayed_evs", 0),
            "avg_delay_min": schedule_result.get("avg_delay_min", 0),
            "total_cost_rs": schedule_result.get("total_cost_rs", 0),
        },
    }

    if feasibility_issues:
        optimised_metrics["feasibility_issues"] = feasibility_issues

    state.optimised_metrics = optimised_metrics
    state.allocated_evs = allocations
    state.is_optimised = True

    # Calculate comparison
    comparison = None
    if state.baseline_metrics:
        b = state.baseline_metrics
        o = optimised_metrics
        comparison = {
            "wait_reduction_pct": round(
                (b["avg_wait_min"] - o["avg_wait_min"]) / max(b["avg_wait_min"], 0.1) * 100, 1
            ),
            "queue_reduction_pct": round(
                (b["avg_queue_length"] - o["avg_queue_length"]) / max(b["avg_queue_length"], 0.1) * 100, 1
            ),
            "peak_load_reduction_pct": round(
                (b["peak_grid_utilisation"] - o["peak_grid_utilisation"]) / max(b["peak_grid_utilisation"], 0.1) * 100, 1
            ),
            "overload_reduction": b["grid_overload_events"] - o["grid_overload_events"],
            "imbalance_reduction_pct": round(
                (b["load_imbalance"] - o["load_imbalance"]) / max(b["load_imbalance"], 0.1) * 100, 1
            ),
        }

    # Prices after optimisation
    prices = calculate_all_prices(state.stations, state.predictions)

    return {
        "message": f"ChargeFlow AI optimised {n} EVs across {len(state.stations)} stations.",
        "allocations": allocations,
        "schedule": schedule_result,
        "optimised_metrics": optimised_metrics,
        "baseline_metrics": state.baseline_metrics,
        "comparison": comparison,
        "stations": state.stations,
        "prices": prices,
        "congestion_alerts": state.congestion_alerts,
    }


@router.post("/simulate/reset")
def simulate_reset():
    from backend.app.api.stations import get_state

    state = get_state()
    state.reset()

    return {
        "message": "Simulation reset to normal state.",
        "scenario": state.scenario,
        "stations": state.stations,
    }


@router.get("/simulation/state")
def simulation_state():
    from backend.app.api.stations import get_state

    state = get_state()

    prices = calculate_all_prices(state.stations, state.predictions)

    return {
        **state.to_dict(),
        "prices": prices,
    }


@router.get("/metrics")
def metrics():
    from backend.app.api.stations import get_state

    state = get_state()

    # KPI calculations from live state
    total_chargers = sum(s["total_chargers"] for s in state.stations)
    active_chargers = total_chargers - sum(s["available_chargers"] for s in state.stations)
    total_queue = sum(s["queue_length"] for s in state.stations)

    # Calculate live average wait time across all stations using exact station queue estimates
    prices = calculate_all_prices(state.stations, state.predictions)
    avg_wait = sum(p["estimated_wait_min"] for p in prices) / max(len(prices), 1)

    station_utils = [s["current_load_kw"] / s["grid_limit_kw"] for s in state.stations]
    avg_grid_load = sum(station_utils) / max(len(station_utils), 1) * 100
    congested = sum(1 for u in station_utils if u > 0.8)

    kpis = {
        "active_evs": total_queue + active_chargers,
        "charging_evs": active_chargers,
        "avg_wait_min": round(avg_wait, 1),
        "avg_grid_load_pct": round(avg_grid_load, 1),
        "congested_stations": congested,
        "total_stations": len(state.stations),
        "total_chargers": total_chargers,
        "available_chargers": sum(s["available_chargers"] for s in state.stations),
        "total_queue": total_queue,
    }

    # Model metrics
    model_metrics = None
    try:
        from ml.predict import get_model_metrics
        model_metrics = get_model_metrics()
    except Exception:
        pass

    return {
        "kpis": kpis,
        "scenario": state.scenario,
        "is_peak": state.is_peak,
        "is_optimised": state.is_optimised,
        "baseline_metrics": state.baseline_metrics,
        "optimised_metrics": state.optimised_metrics,
        "model_metrics": model_metrics,
    }
