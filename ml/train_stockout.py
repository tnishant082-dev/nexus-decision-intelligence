"""Product stockout-risk classifier from inventory snapshots (honest holdout)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from ml.paths import DB, EXPERIMENTS, REGISTRY, MODELS
from ml.tracking import log_run


def load_features(db: Path = DB) -> pd.DataFrame:
    con = duckdb.connect(str(db), read_only=True)
    df = con.execute("""
        SELECT p.product_key, p.abc_class,
               AVG(i.stockout_flag::DOUBLE) AS stockout_rate,
               AVG(i.on_hand_units) AS avg_on_hand,
               AVG(i.demand_units) AS avg_demand,
               AVG(i.unfilled_units) AS avg_unfilled,
               AVG(i.backorder_units) AS avg_backorder,
               AVG(i.safety_stock_units) AS avg_safety
        FROM fact_inventory i
        JOIN dim_product p ON i.product_key = p.product_key
        GROUP BY 1, 2
    """).df()
    con.close()
    df["coverage"] = df["avg_on_hand"] / df["avg_demand"].clip(lower=1e-6)
    df["high_risk"] = (df["stockout_rate"] >= df["stockout_rate"].median()).astype(int)
    df["abc_code"] = df["abc_class"].astype("category").cat.codes
    return df


def train(db: Path = DB) -> dict:
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    df = load_features(db)
    feats = ["avg_on_hand", "avg_demand", "avg_unfilled", "avg_backorder", "avg_safety", "coverage", "abc_code"]
    X = df[feats].fillna(0)
    y = df["high_risk"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    clf = GradientBoostingClassifier(random_state=42, max_depth=3)
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else None
    p, r, f1, _ = precision_recall_fscore_support(y_test, pred, average="binary", zero_division=0)
    run_id = datetime.now(timezone.utc).strftime("stockout_%Y%m%dT%H%M%SZ")
    model_path = MODELS / f"{run_id}.joblib"
    joblib.dump({"model": clf, "features": feats, "label": "stockout_rate >= median"}, model_path)
    metrics = {
        "run_id": run_id,
        "task": "stockout_risk_proxy",
        "products": int(len(df)),
        "auc": round(auc, 4) if auc is not None else None,
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "label": "high_risk if product-level mean stockout_flag >= median (in-sample construction)",
        "honesty_note": "Label uses the same stockout history as some features (esp. avg_unfilled). Treat as a ranking demo, not a causal risk model.",
        "model_path": str(model_path),
    }
    log_run("stockout_risk", {"label": metrics["label"]}, {k: metrics[k] for k in ("auc", "precision", "recall", "f1") if metrics[k] is not None})
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps(metrics, indent=2))
    (REGISTRY / "stockout_v1.json").write_text(json.dumps({
        "model_id": "stockout_v1",
        "run_id": run_id,
        "stage": "staging",
        "metrics": {k: metrics[k] for k in ("auc", "precision", "recall", "f1", "model_path")},
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    return metrics


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
