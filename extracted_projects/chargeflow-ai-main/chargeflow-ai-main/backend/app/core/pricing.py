"""
ChargeFlow AI — Dynamic Incentive Pricing
===========================================
Simple, transparent pricing: increase price at congested stations,
decrease at underutilised ones to encourage demand redistribution.
"""

BASE_PRICE = 16.0  # ₹/kWh

# Pricing parameters
CONGESTION_SURCHARGE_MAX = 5.0   # Max ₹ surcharge at 100% utilisation
UNDERUTIL_DISCOUNT_MAX = 4.0     # Max ₹ discount at 0% utilisation
QUEUE_SURCHARGE_PER_EV = 0.5     # ₹ surcharge per EV in queue


def calculate_price(station: dict, predictions: dict | None = None) -> dict:
    """
    Calculate dynamic price for a station based on current and predicted load.

    Returns price breakdown with explanation.
    """
    utilisation = station["current_load_kw"] / max(station["grid_limit_kw"], 1)
    queue = station.get("queue_length", 0)

    # Congestion component
    if utilisation > 0.5:
        # Linear scale from 0.5 to 1.0 → 0 to max surcharge
        congestion_adj = CONGESTION_SURCHARGE_MAX * (utilisation - 0.5) / 0.5
    else:
        # Discount for underutilisation
        congestion_adj = -UNDERUTIL_DISCOUNT_MAX * (0.5 - utilisation) / 0.5

    # Queue component
    queue_adj = min(queue * QUEUE_SURCHARGE_PER_EV, 3.0)

    # Predicted demand adjustment
    forecast_adj = 0.0
    if predictions and station["station_id"] in predictions:
        pred = predictions[station["station_id"]]
        risk = pred.get("congestion_risk", 0)
        if risk > 0.7:
            forecast_adj = 1.5
        elif risk > 0.4:
            forecast_adj = 0.5

    final_price = round(BASE_PRICE + congestion_adj + queue_adj + forecast_adj, 1)
    final_price = max(10.0, min(25.0, final_price))  # Clamp to reasonable range

    # Estimated wait time based on queue
    available = station.get("available_chargers", 0)
    if available > 0 and queue <= available:
        wait_min = 0
    else:
        excess_queue = max(0, queue - available)
        wait_min = excess_queue * 12  # ~12 min per queue position

    return {
        "station_id": station["station_id"],
        "station_name": station["name"],
        "base_price": BASE_PRICE,
        "congestion_adjustment": round(congestion_adj, 1),
        "queue_adjustment": round(queue_adj, 1),
        "forecast_adjustment": round(forecast_adj, 1),
        "final_price": final_price,
        "estimated_wait_min": wait_min,
        "utilisation_pct": round(utilisation * 100, 1),
        "incentive": "DISCOUNT" if final_price < BASE_PRICE else ("SURCHARGE" if final_price > BASE_PRICE else "STANDARD"),
        "savings_vs_base": round(BASE_PRICE - final_price, 1) if final_price < BASE_PRICE else 0,
    }


def calculate_all_prices(stations: list[dict], predictions: dict | None = None) -> list[dict]:
    """Calculate prices for all stations."""
    prices = [calculate_price(s, predictions) for s in stations]
    # Mark the best deal
    prices.sort(key=lambda x: x["final_price"])
    for i, p in enumerate(prices):
        p["best_value"] = i == 0
    # Sort back by station_id
    prices.sort(key=lambda x: x["station_id"])
    return prices
