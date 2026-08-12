"""Simple RFM-style churn classifier using real dim_customer + fact_orders."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from ml.paths import DB, EXPERIMENTS, REGISTRY, MODELS

def load_customer_features(db: Path = DB) -> pd.DataFrame:
    con = duckdb.connect(str(db), read_only=True)
    # Use last order date in extract as "today"
    max_date = con.execute("SELECT MAX(date)::DATE FROM dim_date d JOIN fact_orders o ON o.order_date_key=d.date_key").fetchone()[0]
    df = con.execute(f"""
        SELECT c.customer_key, c.segment,
               COUNT(DISTINCT o.order_id) AS frequency,
               SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END) AS monetary,
               MAX(d.date)::DATE AS last_order,
               MIN(d.date)::DATE AS first_order,
               AVG(o.is_otif::DOUBLE) AS avg_otif,
               AVG(o.is_late::DOUBLE) AS avg_late
        FROM dim_customer c
        JOIN fact_orders o ON c.customer_key = o.customer_key
        JOIN dim_date d ON o.order_date_key = d.date_key
        GROUP BY 1, 2
    """).df()
    con.close()
    df["last_order"] = pd.to_datetime(df["last_order"])
    df["first_order"] = pd.to_datetime(df["first_order"])
    asof = pd.Timestamp(max_date)
    df["recency_days"] = (asof - df["last_order"]).dt.days
    # churn label: no order in last 180 days of extract window (honest proxy)
    df["churned"] = (df["recency_days"] > 180).astype(int)
    df["tenure_days"] = (df["last_order"] - df["first_order"]).dt.days.clip(lower=0)
    return df

def train(db: Path = DB) -> dict:
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = load_customer_features(db)
    features = ["frequency", "monetary", "recency_days", "tenure_days", "avg_otif", "avg_late"]
    X = df[features].fillna(0)
    y = df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    # NOTE: recency_days is strongly correlated with the label by construction —
    # we still train for demo but document the leakage risk and also report a
    # leakage-aware variant excluding recency.
    clf = GradientBoostingClassifier(random_state=42, max_depth=3)
    clf.fit(X_train, y_train)
    auc = float(roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1]))

    # leakage-aware: drop recency (registry model)
    feats2 = ["frequency", "monetary", "tenure_days", "avg_otif", "avg_late"]
    clf2 = GradientBoostingClassifier(random_state=42, max_depth=3)
    clf2.fit(X_train[feats2], y_train)
    proba2 = clf2.predict_proba(X_test[feats2])[:, 1]
    pred2 = (proba2 >= 0.5).astype(int)
    auc2 = float(roc_auc_score(y_test, proba2))
    p, r, f1, _ = precision_recall_fscore_support(y_test, pred2, average="binary", zero_division=0)

    run_id = datetime.now(timezone.utc).strftime("churn_%Y%m%dT%H%M%SZ")
    model_path = MODELS / f"{run_id}.joblib"
    joblib.dump({"model": clf2, "features": feats2, "label_def": "recency_days>180"}, model_path)

    metrics = {
        "run_id": run_id,
        "task": "customer_churn_proxy",
        "customers": int(len(df)),
        "churn_rate": round(float(y.mean()), 4),
        "auc_with_recency_LEAKY": round(auc, 4),
        "auc_without_recency": round(auc2, 4),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "label": "churned if no order in last 180 days of extract (2015-2018 window)",
        "honesty_note": "AUC with recency is inflated by label leakage; production registry uses without-recency model.",
        "model_path": str(model_path),
    }
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps(metrics, indent=2))
    (REGISTRY / "churn_v1.json").write_text(json.dumps({
        "model_id": "churn_v1", "run_id": run_id, "stage": "staging",
        "metrics": {"auc_without_recency": metrics["auc_without_recency"], "churn_rate": metrics["churn_rate"], "model_path": metrics["model_path"]},
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    return metrics

if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
