"""Isolation Forest on warehouse/week OTIF & late proxies — anomaly scores."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ml.paths import DB, EXPERIMENTS, REGISTRY, MODELS

def load_series(db: Path = DB) -> pd.DataFrame:
    con = duckdb.connect(str(db), read_only=True)
    df = con.execute("""
        SELECT d.week_start_date::DATE AS week_start,
               o.warehouse_key,
               AVG(o.is_otif::DOUBLE) AS otif_rate,
               AVG(o.is_late::DOUBLE) AS late_rate,
               AVG(o.is_perfect_order::DOUBLE) AS perfect_rate,
               SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END) AS revenue,
               COUNT(*) AS lines
        FROM fact_orders o
        JOIN dim_date d ON o.order_date_key = d.date_key
        GROUP BY 1, 2
        HAVING COUNT(*) >= 20
        ORDER BY 1, 2
    """).df()
    con.close()
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df

def train(db: Path = DB) -> dict:
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = load_series(db)
    feats = ["otif_rate", "late_rate", "perfect_rate", "revenue", "lines"]
    X = df[feats].fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(Xs)
    scores = -model.decision_function(Xs)  # higher = more anomalous
    df = df.copy()
    df["anomaly_score"] = scores
    df["is_anomaly"] = (model.predict(Xs) == -1).astype(int)
    top = df.sort_values("anomaly_score", ascending=False).head(15)

    run_id = datetime.now(timezone.utc).strftime("anomaly_%Y%m%dT%H%M%SZ")
    model_path = MODELS / f"{run_id}.joblib"
    joblib.dump({"model": model, "scaler": scaler, "features": feats}, model_path)
    metrics = {
        "run_id": run_id,
        "task": "otif_late_anomaly",
        "rows": int(len(df)),
        "anomaly_count": int(df["is_anomaly"].sum()),
        "contamination": 0.05,
        "top_anomalies": top[["week_start", "warehouse_key", "otif_rate", "late_rate", "anomaly_score"]]
            .assign(week_start=lambda x: x["week_start"].astype(str))
            .to_dict(orient="records"),
        "model_path": str(model_path),
    }
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps(metrics, indent=2))
    (REGISTRY / "anomaly_otif_v1.json").write_text(json.dumps({
        "model_id": "anomaly_otif_v1", "run_id": run_id, "stage": "staging",
        "metrics": {k: metrics[k] for k in ("rows", "anomaly_count", "contamination", "model_path")},
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    # persist scored table for UI
    out_csv = MODELS / f"{run_id}_scores.csv"
    df.assign(week_start=df["week_start"].astype(str)).to_csv(out_csv, index=False)
    metrics["scores_path"] = str(out_csv)
    return metrics

if __name__ == "__main__":
    print(json.dumps(train(), indent=2)[:2000])
