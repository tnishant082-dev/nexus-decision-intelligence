"""Batch + online predict helpers for registered models."""
from __future__ import annotations
import json
from pathlib import Path

import joblib
import pandas as pd

from ml.paths import REGISTRY, MODELS, ROOT


def _resolve(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _reg(model_id: str) -> dict:
    path = REGISTRY / f"{model_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Registry entry missing: {model_id}. Train models first.")
    return json.loads(path.read_text())


def _bundle(model_id: str):
    reg = _reg(model_id)
    run_id = reg["run_id"]
    # forecast/anomaly/churn store metrics.model_path or MODELS/{run_id}.joblib
    metrics = reg.get("metrics") or {}
    if "model_path" in metrics:
        return joblib.load(_resolve(metrics["model_path"]))
    path = MODELS / f"{run_id}.joblib"
    if not path.exists():
        raise FileNotFoundError(path)
    return joblib.load(path)


def predict_demand(rows: list[dict]) -> list[dict]:
    bundle = _bundle("demand_forecast_v1")
    model, features, cat_map = bundle["model"], bundle["features"], bundle["cat_map"]
    out = []
    for r in rows:
        row = {f: r.get(f, 0) for f in features if f != "cat_code"}
        row["cat_code"] = cat_map.get(r.get("category_name"), 0)
        X = pd.DataFrame([row])[features]
        pred = float(model.predict(X)[0])
        out.append({"category_name": r.get("category_name"), "predicted_units": round(pred, 2)})
    return out


def score_anomaly(rows: list[dict]) -> list[dict]:
    bundle = _bundle("anomaly_otif_v1")
    # anomaly registry may not embed model_path — load by run_id
    reg = _reg("anomaly_otif_v1")
    path = MODELS / f"{reg['run_id']}.joblib"
    bundle = joblib.load(path)
    model, scaler, feats = bundle["model"], bundle["scaler"], bundle["features"]
    X = pd.DataFrame(rows)[feats].fillna(0).values
    Xs = scaler.transform(X)
    scores = (-model.decision_function(Xs)).tolist()
    flags = (model.predict(Xs) == -1).astype(int).tolist()
    return [{"anomaly_score": round(float(s), 4), "is_anomaly": int(f)} for s, f in zip(scores, flags)]


def predict_churn(rows: list[dict]) -> list[dict]:
    reg = _reg("churn_v1")
    bundle = joblib.load(MODELS / f"{reg['run_id']}.joblib")
    model, features = bundle["model"], bundle["features"]
    X = pd.DataFrame(rows)[features].fillna(0)
    proba = model.predict_proba(X)[:, 1]
    return [{"churn_probability": round(float(p), 4)} for p in proba]


def predict_stockout(rows: list[dict]) -> list[dict]:
    bundle = _bundle("stockout_v1")
    model, features = bundle["model"], bundle["features"]
    X = pd.DataFrame(rows)[features].fillna(0)
    proba = model.predict_proba(X)[:, 1]
    return [{"stockout_risk": round(float(p), 4)} for p in proba]
