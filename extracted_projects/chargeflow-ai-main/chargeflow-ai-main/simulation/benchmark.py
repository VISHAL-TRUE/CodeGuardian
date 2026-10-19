"""
ChargeFlow AI — End-to-End Benchmark Runner
============================================
Runs the Peak Demand scenario through both Baseline and ChargeFlow AI
to generate concrete before vs after performance comparison metrics.
"""

import copy
import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from simulation.simulator import SimulationState
from backend.app.core.scoring import rank_stations
from backend.app.core.optimizer import schedule_charging
from backend.app.core.pricing import calculate_all_prices


def run_full_benchmark():
    # Initialize fresh simulation state
    state = SimulationState()

    # Step 1: Inject Peak Demand
    state.inject_peak_demand()
    baseline = state.baseline_metrics

    # Step 2: Try to load ML predictions if available
    try:
        from ml.predict import predict_all_stations
        state.predictions = predict_all_stations(state.stations)
    except Exception as e:
        print(f"Prediction notice: {e}")

    # Step 3: Run ChargeFlow AI Optimization
    allocations = []
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
        for ws in working_stations:
            if ws["station_id"] == best["station_id"]:
                ws["queue_length"] += 1
                ws["current_load_kw"] += min(ev["max_charge_rate_kw"], 60)
                if ws["available_chargers"] > 0:
                    ws["available_chargers"] -= 1
                break

    schedule_res = schedule_charging(state.pending_evs, state.stations, allocations)

    # Update state stations using PuLP-scheduled power (active vs deferred)
    pulp_schedules = schedule_res.get("schedules", [])
    station_active_power = {}
    station_active_count = {}
    station_deferred_count = {}

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

    total_wait = 0
    total_queue = 0
    grid_overloads = 0
    for s in state.stations:
        excess_q = max(0, s["queue_length"] - s["total_chargers"])
        total_queue += s["queue_length"]
        total_wait += excess_q * 12
        if s["current_load_kw"] > s["grid_limit_kw"]:
            grid_overloads += 1

    n = len(state.pending_evs)
    station_loads = [s["current_load_kw"] / s["grid_limit_kw"] for s in state.stations]
    load_imbalance = max(station_loads) - min(station_loads) if station_loads else 0

    optimised = {
        "strategy": "ChargeFlow AI",
        "avg_wait_min": round(total_wait / n, 1),
        "avg_queue_length": round(total_queue / len(state.stations), 1),
        "peak_grid_utilisation": round(max(station_loads) * 100, 1),
        "grid_overload_events": grid_overloads,
        "load_imbalance": round(load_imbalance * 100, 1),
        "total_evs": n,
    }

    # Comparison metrics
    wait_reduction = round((baseline["avg_wait_min"] - optimised["avg_wait_min"]) / max(baseline["avg_wait_min"], 0.1) * 100, 1)
    queue_reduction = round((baseline["avg_queue_length"] - optimised["avg_queue_length"]) / max(baseline["avg_queue_length"], 0.1) * 100, 1)
    peak_load_reduction = round((baseline["peak_grid_utilisation"] - optimised["peak_grid_utilisation"]) / max(baseline["peak_grid_utilisation"], 0.1) * 100, 1)
    overload_reduction = baseline["grid_overload_events"] - optimised["grid_overload_events"]
    imbalance_reduction = round((baseline["load_imbalance"] - optimised["load_imbalance"]) / max(baseline["load_imbalance"], 0.1) * 100, 1)

    print("\n" + "=" * 70)
    print("           CHARGEFLOW AI — BENCHMARK EVALUATION SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<30} | {'Uncoordinated Baseline':<22} | {'ChargeFlow AI':<16} | {'Improvement'}")
    print("-" * 70)
    print(f"{'Average Waiting Time':<30} | {str(baseline['avg_wait_min']) + ' min':<22} | {str(optimised['avg_wait_min']) + ' min':<16} | -{wait_reduction}%")
    print(f"{'Average Station Queue':<30} | {str(baseline['avg_queue_length']) + ' EVs':<22} | {str(optimised['avg_queue_length']) + ' EVs':<16} | -{queue_reduction}%")
    print(f"{'Peak Grid Utilisation':<30} | {str(baseline['peak_grid_utilisation']) + '%' :<22} | {str(optimised['peak_grid_utilisation']) + '%' :<16} | -{peak_load_reduction}%")
    print(f"{'Grid Overload Incidents':<30} | {str(baseline['grid_overload_events']) :<22} | {str(optimised['grid_overload_events']) :<16} | -{overload_reduction} events")
    print(f"{'Station Load Imbalance':<30} | {str(baseline['load_imbalance']) + '%' :<22} | {str(optimised['load_imbalance']) + '%' :<16} | -{imbalance_reduction}%")
    print("=" * 70 + "\n")

    return {
        "baseline": baseline,
        "optimised": optimised,
        "improvements": {
            "wait_reduction_pct": wait_reduction,
            "queue_reduction_pct": queue_reduction,
            "peak_load_reduction_pct": peak_load_reduction,
            "overload_reduction": overload_reduction,
            "imbalance_reduction_pct": imbalance_reduction,
        }
    }


if __name__ == "__main__":
    run_full_benchmark()
