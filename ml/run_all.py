#!/usr/bin/env python3
"""Train all NEXUS ML models (forecast, anomaly, churn)."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.train_forecast import train as train_forecast
from ml.train_anomaly import train as train_anomaly
from ml.train_churn import train as train_churn

def main():
    results = {
        "forecast": train_forecast(),
        "anomaly": train_anomaly(),
        "churn": train_churn(),
    }
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "top_anomalies"} for k, v in results.items()}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
