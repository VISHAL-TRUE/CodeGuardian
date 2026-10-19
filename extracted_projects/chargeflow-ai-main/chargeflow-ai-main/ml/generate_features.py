"""
ChargeFlow AI — Feature Engineering for Demand Forecasting
============================================================
Generates features from charging_sessions.csv for model training.
"""

import os
import pandas as pd
import numpy as np

SEED = 42
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def generate_features() -> pd.DataFrame:
    """
    Load charging sessions and engineer features for demand prediction.

    Target: demand (number of active sessions per station per hour)
    """
    path = os.path.join(DATA_DIR, "charging_sessions.csv")
    df = pd.read_csv(path, parse_dates=["timestamp"])

    # Aggregate hourly demand per station
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Group by station, date, hour → count sessions as demand proxy
    hourly = (
        df.groupby(["station_id", "date", "hour", "day_of_week", "is_weekend"])
        .agg(
            demand=("session_id", "count"),
            avg_energy=("energy_requested_kwh", "mean"),
            avg_power=("charging_power_kw", "mean"),
            avg_duration=("charging_duration_min", "mean"),
            avg_soc=("battery_soc", "mean"),
        )
        .reset_index()
    )

    # Encode station_id as numeric
    station_map = {sid: i for i, sid in enumerate(sorted(hourly["station_id"].unique()))}
    hourly["station_num"] = hourly["station_id"].map(station_map)

    # Rolling features (per station, sorted by date+hour)
    hourly = hourly.sort_values(["station_id", "date", "hour"])
    for window in [3, 6, 12]:
        hourly[f"rolling_demand_{window}h"] = (
            hourly.groupby("station_id")["demand"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )

    # Lag features
    hourly["demand_lag_1h"] = hourly.groupby("station_id")["demand"].shift(1).fillna(0)
    hourly["demand_lag_24h"] = hourly.groupby("station_id")["demand"].shift(24).fillna(0)

    # Peak hour indicator
    hourly["is_morning_peak"] = ((hourly["hour"] >= 8) & (hourly["hour"] <= 10)).astype(int)
    hourly["is_evening_peak"] = ((hourly["hour"] >= 17) & (hourly["hour"] <= 20)).astype(int)

    # Hour sin/cos encoding for cyclical nature
    hourly["hour_sin"] = np.sin(2 * np.pi * hourly["hour"] / 24)
    hourly["hour_cos"] = np.cos(2 * np.pi * hourly["hour"] / 24)

    # Day sin/cos
    hourly["dow_sin"] = np.sin(2 * np.pi * hourly["day_of_week"] / 7)
    hourly["dow_cos"] = np.cos(2 * np.pi * hourly["day_of_week"] / 7)

    hourly = hourly.dropna()

    # Save features
    out_path = os.path.join(DATA_DIR, "features.csv")
    hourly.to_csv(out_path, index=False)
    print(f"  ✓ features.csv — {len(hourly)} rows, {len(hourly.columns)} columns")

    return hourly


FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend", "station_num",
    "avg_energy", "avg_power", "avg_duration",
    "rolling_demand_3h", "rolling_demand_6h", "rolling_demand_12h",
    "demand_lag_1h", "demand_lag_24h",
    "is_morning_peak", "is_evening_peak",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
]


if __name__ == "__main__":
    print("Generating features…")
    df = generate_features()
    print(f"Feature columns: {FEATURE_COLS}")
    print(df[FEATURE_COLS + ['demand']].describe())
