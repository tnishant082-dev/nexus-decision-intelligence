"""Category × week demand forecast with sklearn GradientBoosting (honest holdout)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.paths import DB, EXPERIMENTS, REGISTRY, MODELS

def load_weekly(db: Path = DB) -> pd.DataFrame:
    con = duckdb.connect(str(db), read_only=True)
    df = con.execute("""
        SELECT week_start_date::DATE AS week_start, category_name,
               SUM(units) AS units, SUM(revenue) AS revenue, SUM(orders) AS orders
        FROM v_demand_weekly
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).df()
    con.close()
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df

def featurize(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for cat, g in df.groupby("category_name"):
        g = g.sort_values("week_start").copy()
        g["lag1"] = g["units"].shift(1)
        g["lag2"] = g["units"].shift(2)
        g["lag4"] = g["units"].shift(4)
        g["roll4"] = g["units"].rolling(4, min_periods=1).mean().shift(1)
        g["weekofyear"] = g["week_start"].dt.isocalendar().week.astype(int)
        g["month"] = g["week_start"].dt.month
        parts.append(g)
    out = pd.concat(parts, ignore_index=True).dropna()
    return out

def train(db: Path = DB) -> dict:
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    raw = load_weekly(db)
    feat = featurize(raw)
    # time-based holdout: last 16 distinct week_starts (global), keep all categories
    weeks = sorted(feat["week_start"].unique())
    holdout_weeks = set(weeks[-16:]) if len(weeks) > 20 else set(weeks[-max(4, len(weeks)//5):])
    train_df = feat[~feat["week_start"].isin(holdout_weeks)]
    test_df = feat[feat["week_start"].isin(holdout_weeks)]

    features = ["lag1", "lag2", "lag4", "roll4", "weekofyear", "month"]
    # encode category as codes for tree model
    cats = sorted(feat["category_name"].unique())
    cat_map = {c: i for i, c in enumerate(cats)}
    for d in (train_df, test_df, feat):
        d["cat_code"] = d["category_name"].map(cat_map)

    X_train = train_df[features + ["cat_code"]]
    y_train = train_df["units"]
    X_test = test_df[features + ["cat_code"]]
    y_test = test_df["units"]

    model = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.08, max_iter=120, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mape = float(np.mean(np.abs((y_test - pred) / np.clip(np.abs(y_test), 1, None))) * 100)
    wape = float(np.sum(np.abs(y_test - pred)) / max(np.sum(np.abs(y_test)), 1) * 100)
    # naive lag1 baseline
    naive = test_df["lag1"].values
    naive_mae = float(mean_absolute_error(y_test, naive))

    run_id = datetime.now(timezone.utc).strftime("forecast_%Y%m%dT%H%M%SZ")
    model_path = MODELS / f"{run_id}.joblib"
    joblib.dump({"model": model, "features": features + ["cat_code"], "cat_map": cat_map}, model_path)

    metrics = {
        "run_id": run_id,
        "task": "demand_forecast_category_week",
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape_pct": round(mape, 2),
        "wape_pct": round(wape, 2),
        "naive_lag1_mae": round(naive_mae, 2),
        "lift_vs_naive_mae_pct": round((1 - mae / naive_mae) * 100, 2) if naive_mae else None,
        "model_path": str(model_path),
        "note": "Holdout = last ~16 week_starts. Prefer WAPE over MAPE on sparse categories; compare MAE to lag-1 naive.",
    }
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps(metrics, indent=2))
    registry = {
        "model_id": "demand_forecast_v1",
        "run_id": run_id,
        "stage": "staging",
        "metrics": metrics,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    (REGISTRY / "demand_forecast_v1.json").write_text(json.dumps(registry, indent=2))
    return metrics

if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
