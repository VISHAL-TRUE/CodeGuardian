"""
ChargeFlow AI — Baseline Simulation Module
===========================================
Implements the naive "Nearest Available Station" (First-Come, First-Served)
baseline strategy for direct benchmarking against ChargeFlow AI optimization.
"""

import copy
import math
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from simulation.simulator import SimulationState, haversine_km


def run_baseline_benchmark(ev_burst_count: int = 12) -> dict:
    """
    Runs deterministic baseline on a fresh simulation state and returns detailed metrics.
    """
    state = SimulationState()
    state.inject_peak_demand()
    baseline = state.baseline_metrics
    return baseline


if __name__ == "__main__":
    print("=" * 60)
    print("  ChargeFlow AI — Uncoordinated Baseline Benchmark")
    print("=" * 60)
    metrics = run_baseline_benchmark()
    print(f"Strategy:                {metrics['strategy']}")
    print(f"Total Incoming EVs:      {metrics['total_evs']}")
    print(f"Average Waiting Time:    {metrics['avg_wait_min']} min")
    print(f"Average Queue Length:    {metrics['avg_queue_length']} EVs")
    print(f"Peak Grid Utilisation:   {metrics['peak_grid_utilisation']}%")
    print(f"Grid Overload Incidents: {metrics['grid_overload_events']}")
    print(f"Station Load Imbalance:  {metrics['load_imbalance']}%")
    print("-" * 60)
    print("Station Load Breakdown:")
    for s in metrics["station_states"]:
        print(f"  [{s['station_id']}] Load: {s['current_load_kw']} / {s['grid_limit_kw']} kW ({s['utilisation_pct']}%) | Queue: {s['queue_length']}")
    print("=" * 60)
