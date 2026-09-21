"""Category × week demand forecast with sklearn GradientBoosting (honest holdout)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.estimators import available_regressors
from ml.explain import shap_values, tree_importance
from ml.paths import DB, EXPERIMENTS, REGISTRY, MODELS
from ml.tracking import log_run

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

    naive = test_df["lag1"].values
    naive_mae = float(mean_absolute_error(y_test, naive))
    comparison = []
    fitted = {}
    for name, est in available_regressors().items():
        est.fit(X_train, y_train)
        pred_i = est.predict(X_test)
        mae_i = float(mean_absolute_error(y_test, pred_i))
        rmse_i = float(np.sqrt(mean_squared_error(y_test, pred_i)))
        comparison.append({
            "estimator": name,
            "mae": round(mae_i, 2),
            "rmse": round(rmse_i, 2),
            "naive_lag1_mae": round(naive_mae, 2),
            "lift_vs_naive_mae_pct": round((1 - mae_i / naive_mae) * 100, 2) if naive_mae else None,
        })
        fitted[name] = (est, pred_i, mae_i)

    # Registry always uses sklearn HistGB so serving stays dependency-light.
    model = fitted["sklearn_hist_gbr"][0]
    pred = fitted["sklearn_hist_gbr"][1]
    mae = fitted["sklearn_hist_gbr"][2]
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mape = float(np.mean(np.abs((y_test - pred) / np.clip(np.abs(y_test), 1, None))) * 100)
    wape = float(np.sum(np.abs(y_test - pred)) / max(np.sum(np.abs(y_test)), 1) * 100)

    run_id = datetime.now(timezone.utc).strftime("forecast_%Y%m%dT%H%M%SZ")
    model_path = MODELS / f"{run_id}.joblib"
    joblib.dump({"model": model, "features": features + ["cat_code"], "cat_map": cat_map}, model_path)

    importance = tree_importance(model, features + ["cat_code"])
    shap_rep = shap_values(model, X_test, features + ["cat_code"])

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
        "registered_estimator": "sklearn_hist_gbr",
        "comparison": comparison,
        "feature_importance": importance,
        "shap": shap_rep,
        "note": "Holdout = last ~16 week_starts. Prefer WAPE over MAPE on sparse categories; compare MAE to lag-1 naive. XGBoost/LightGBM appear in comparison only if installed.",
    }
    log_run("demand_forecast", {"estimator": "sklearn_hist_gbr", "holdout_weeks": len(holdout_weeks)}, {
        k: metrics[k] for k in ("mae", "rmse", "mape_pct", "wape_pct", "naive_lag1_mae", "lift_vs_naive_mae_pct")
    })
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps(metrics, indent=2, default=str))
    (EXPERIMENTS / "forecast_comparison.json").write_text(json.dumps({
        "run_id": run_id,
        "comparison": comparison,
        "registered": "sklearn_hist_gbr",
        "note": "Only estimators that imported successfully were fit.",
    }, indent=2))
    registry = {
        "model_id": "demand_forecast_v1",
        "run_id": run_id,
        "stage": "staging",
        "metrics": metrics,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    (REGISTRY / "demand_forecast_v1.json").write_text(json.dumps(registry, indent=2, default=str))
    return metrics

if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
