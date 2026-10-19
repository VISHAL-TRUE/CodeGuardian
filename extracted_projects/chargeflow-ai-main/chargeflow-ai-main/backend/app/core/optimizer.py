"""
ChargeFlow AI — Grid-Aware Charging Scheduler (PuLP MILP)
==========================================================
Uses Mixed Integer Linear Programming to optimally schedule
charging power across stations while respecting grid constraints.
"""

import math
from typing import Any

try:
    import pulp
except ImportError:
    pulp = None


def schedule_charging(
    evs: list[dict],
    stations: list[dict],
    allocations: list[dict],
) -> dict:
    """
    Given EV assignments to stations, schedule charging power for each EV
    to minimise total cost while respecting grid limits.

    Each allocation dict must have: ev_id, station_id
    Each ev dict must have: ev_id, current_soc, target_soc, max_charge_rate_kw
    Each station dict must have: station_id, grid_limit_kw, current_load_kw,
                                  max_power_kw, total_chargers, price_per_kwh

    Returns schedule with per-EV power, delays, and feasibility status.
    """
    if pulp is None:
        return _fallback_schedule(evs, stations, allocations)

    # Build station lookup
    st_map = {s["station_id"]: s for s in stations}
    ev_map = {e["ev_id"]: e for e in evs}

    # Group allocations by station
    station_evs: dict[str, list[str]] = {}
    for a in allocations:
        sid = a["station_id"]
        station_evs.setdefault(sid, []).append(a["ev_id"])

    schedules = []
    total_cost = 0.0
    total_delay = 0.0
    feasibility_issues = []

    for sid, ev_ids in station_evs.items():
        station = st_map.get(sid)
        if not station:
            continue

        grid_limit = station["grid_limit_kw"]
        base_load = station["current_load_kw"]
        available_headroom = max(0, grid_limit - base_load)
        price = station.get("price_per_kwh", 16.0)
        n_chargers = station["total_chargers"]

        # Create LP problem for this station
        prob = pulp.LpProblem(f"ChargeSchedule_{sid}", pulp.LpMinimize)

        # Decision variables: power for each EV (continuous)
        power_vars = {}
        active_vars = {}  # Binary: is EV active (not delayed)?

        for ev_id in ev_ids:
            ev = ev_map.get(ev_id)
            if not ev:
                continue
            max_rate = ev["max_charge_rate_kw"]
            power_vars[ev_id] = pulp.LpVariable(
                f"power_{ev_id}", lowBound=0, upBound=max_rate, cat="Continuous"
            )
            active_vars[ev_id] = pulp.LpVariable(
                f"active_{ev_id}", cat="Binary"
            )

        if not power_vars:
            continue

        # Objective: minimise weighted combination of:
        #   - total charging cost (power * price)
        #   - delay penalty (inactive EVs)
        cost_weight = 1.0
        delay_weight = 50.0  # Penalise delays heavily

        prob += (
            cost_weight * pulp.lpSum(power_vars[eid] * price for eid in power_vars) +
            delay_weight * pulp.lpSum(1 - active_vars[eid] for eid in active_vars)
        )

        # Constraint 1: Total power at station <= grid headroom
        prob += (
            pulp.lpSum(power_vars[eid] for eid in power_vars) <= available_headroom,
            f"grid_limit_{sid}"
        )

        # Constraint 2: Active EVs limited by charger count
        prob += (
            pulp.lpSum(active_vars[eid] for eid in active_vars) <= n_chargers,
            f"charger_limit_{sid}"
        )

        # Constraint 3: Power linked to active status
        for ev_id in power_vars:
            ev = ev_map.get(ev_id)
            max_rate = ev["max_charge_rate_kw"] if ev else 150
            # If not active, power = 0
            prob += power_vars[ev_id] <= max_rate * active_vars[ev_id], f"link_{ev_id}"
            # Minimum useful charging power if active
            prob += power_vars[ev_id] >= 10 * active_vars[ev_id], f"min_power_{ev_id}"

        # Solve
        try:
            prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=5))
        except Exception as e:
            feasibility_issues.append(f"Solver error at {sid}: {str(e)}")
            # Fallback for this station
            for ev_id in ev_ids:
                ev = ev_map.get(ev_id)
                if not ev:
                    continue
                schedules.append(_fallback_ev_schedule(ev, station))
            continue

        if prob.status != pulp.constants.LpStatusOptimal:
            feasibility_issues.append(
                f"Station {sid}: No optimal solution found (status={pulp.LpStatus[prob.status]}). "
                f"Grid headroom may be insufficient for all EVs."
            )

        # Extract results
        for ev_id in power_vars:
            ev = ev_map.get(ev_id)
            if not ev:
                continue
            power = pulp.value(power_vars[ev_id]) or 0
            is_active = pulp.value(active_vars[ev_id]) or 0
            energy_needed = (ev["target_soc"] - ev["current_soc"]) / 100.0 * 60  # ~60 kWh battery
            duration = (energy_needed / max(power, 1)) * 60 if power > 0 else 0
            delay = 0 if is_active > 0.5 else 15  # 15 min delay if deferred

            cost = power * price * (duration / 60)  # Rs

            schedules.append({
                "ev_id": ev_id,
                "station_id": sid,
                "charging_power_kw": round(power, 1),
                "energy_needed_kwh": round(energy_needed, 1),
                "charging_duration_min": round(duration, 1),
                "delay_min": delay,
                "is_active": is_active > 0.5,
                "estimated_cost_rs": round(cost, 1),
                "feasible": power > 0,
            })
            total_cost += cost
            total_delay += delay

    n = len(schedules) if schedules else 1
    return {
        "schedules": schedules,
        "total_evs_scheduled": len(schedules),
        "active_evs": sum(1 for s in schedules if s.get("is_active")),
        "delayed_evs": sum(1 for s in schedules if not s.get("is_active")),
        "avg_delay_min": round(total_delay / n, 1),
        "total_cost_rs": round(total_cost, 1),
        "feasibility_issues": feasibility_issues,
    }


def _fallback_schedule(evs, stations, allocations):
    """Simple proportional scheduling when PuLP is not available."""
    st_map = {s["station_id"]: s for s in stations}
    ev_map = {e["ev_id"]: e for e in evs}
    schedules = []

    for a in allocations:
        ev = ev_map.get(a["ev_id"])
        station = st_map.get(a["station_id"])
        if ev and station:
            schedules.append(_fallback_ev_schedule(ev, station))

    n = len(schedules) if schedules else 1
    return {
        "schedules": schedules,
        "total_evs_scheduled": len(schedules),
        "active_evs": len(schedules),
        "delayed_evs": 0,
        "avg_delay_min": 0,
        "total_cost_rs": round(sum(s["estimated_cost_rs"] for s in schedules), 1),
        "feasibility_issues": ["PuLP not available — using proportional fallback"],
    }


def _fallback_ev_schedule(ev: dict, station: dict) -> dict:
    headroom = max(0, station["grid_limit_kw"] - station["current_load_kw"])
    power = min(ev["max_charge_rate_kw"], headroom / max(1, station["total_chargers"]), 60)
    power = max(power, 10)
    energy = (ev["target_soc"] - ev["current_soc"]) / 100.0 * 60
    duration = (energy / power) * 60 if power > 0 else 0
    price = station.get("price_per_kwh", 16.0)
    return {
        "ev_id": ev["ev_id"],
        "station_id": station["station_id"],
        "charging_power_kw": round(power, 1),
        "energy_needed_kwh": round(energy, 1),
        "charging_duration_min": round(duration, 1),
        "delay_min": 0,
        "is_active": True,
        "estimated_cost_rs": round(power * price * duration / 60, 1),
        "feasible": True,
    }
