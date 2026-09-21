#!/usr/bin/env python3
"""Train NEXUS ML models and write drift/comparison artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.train_forecast import train as train_forecast, load_weekly, featurize
from ml.train_anomaly import train as train_anomaly
from ml.train_churn import train as train_churn
from ml.train_stockout import train as train_stockout
from ml.drift import run as run_drift


def main():
    forecast = train_forecast()
    results = {
        "forecast": {k: v for k, v in forecast.items() if k not in {"shap", "feature_importance"}},
        "anomaly": train_anomaly(),
        "churn": train_churn(),
        "stockout": train_stockout(),
    }
    feat = featurize(load_weekly())
    weeks = sorted(feat["week_start"].unique())
    mid = weeks[len(weeks) // 2]
    run_drift(feat[feat["week_start"] > mid], feat[feat["week_start"] <= mid], ["units", "revenue", "lag1"])
    slim = {}
    for k, v in results.items():
        slim[k] = {kk: vv for kk, vv in v.items() if kk not in {"top_anomalies", "comparison", "shap", "feature_importance"}}
    print(json.dumps(slim, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
