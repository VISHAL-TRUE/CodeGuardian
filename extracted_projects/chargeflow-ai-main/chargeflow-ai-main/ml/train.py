"""
ChargeFlow AI — Model Training
================================
Trains LightGBM (primary) or RandomForest (fallback) for demand forecasting.
Saves model + metrics to ml/models/.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Try LightGBM first, fall back to sklearn
try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

from sklearn.ensemble import GradientBoostingRegressor

SEED = 42
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend", "station_num",
    "avg_energy", "avg_power", "avg_duration",
    "rolling_demand_3h", "rolling_demand_6h", "rolling_demand_12h",
    "demand_lag_1h", "demand_lag_24h",
    "is_morning_peak", "is_evening_peak",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
]


def train():
    # Load features
    features_path = os.path.join(DATA_DIR, "features.csv")
    if not os.path.exists(features_path):
        print("Features not found. Generating…")
        from generate_features import generate_features
        generate_features()

    df = pd.read_csv(features_path)
    print(f"Training data: {len(df)} rows")

    X = df[FEATURE_COLS].values
    y = df["demand"].values

    # Time-series split for validation
    tscv = TimeSeriesSplit(n_splits=3)
    maes = []
    rmses = []

    for train_idx, val_idx in tscv.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        if HAS_LGBM:
            model = lgb.LGBMRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=10,
                random_state=SEED,
                verbose=-1,
            )
        else:
            model = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                random_state=SEED,
            )

        model.fit(X_tr, y_tr)
        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        maes.append(mae)
        rmses.append(rmse)

    # Train final model on all data
    if HAS_LGBM:
        final_model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=10,
            random_state=SEED,
            verbose=-1,
        )
    else:
        final_model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=SEED,
        )

    final_model.fit(X, y)

    # Save model
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "demand_model.pkl")
    joblib.dump(final_model, model_path)

    # Save metrics
    avg_mae = np.mean(maes)
    avg_rmse = np.mean(rmses)
    metrics = {
        "model_type": "LightGBM" if HAS_LGBM else "GradientBoosting",
        "n_features": len(FEATURE_COLS),
        "feature_names": FEATURE_COLS,
        "cv_folds": 3,
        "mae": round(float(avg_mae), 4),
        "rmse": round(float(avg_rmse), 4),
        "training_samples": len(X),
        "mean_demand": round(float(y.mean()), 2),
        "std_demand": round(float(y.std()), 2),
    }

    # Feature importances
    if HAS_LGBM:
        importances = final_model.feature_importances_
    else:
        importances = final_model.feature_importances_

    fi = sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
    metrics["feature_importances"] = {name: round(float(imp), 4) for name, imp in fi}

    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Model: {metrics['model_type']}")
    print(f"MAE:   {avg_mae:.4f}")
    print(f"RMSE:  {avg_rmse:.4f}")
    print(f"Mean demand: {y.mean():.2f} ± {y.std():.2f}")
    print(f"{'='*50}")
    print(f"\nModel saved: {model_path}")
    print(f"Metrics saved: {metrics_path}")
    print("\nTop features:")
    for name, imp in fi[:8]:
        print(f"  {name}: {imp:.4f}")

    return final_model, metrics


if __name__ == "__main__":
    train()
