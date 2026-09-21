"""File-based experiment tracking (MLflow-compatible optional)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.paths import EXPERIMENTS, ROOT

TRACK = ROOT / "ml" / "tracking"
TRACK.mkdir(parents=True, exist_ok=True)


def log_run(name: str, params: dict, metrics: dict, artifacts: dict | None = None) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime(f"{name}_%Y%m%dT%H%M%SZ")
    payload = {
        "run_id": run_id,
        "name": name,
        "params": params,
        "metrics": metrics,
        "artifacts": artifacts or {},
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "backend": "file",
    }
    path = TRACK / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    (EXPERIMENTS / f"{run_id}.json").write_text(json.dumps({**metrics, "run_id": run_id, "params": params}, indent=2, default=str))
    try:
        import mlflow  # type: ignore

        mlflow.set_experiment("nexus")
        with mlflow.start_run(run_name=name):
            mlflow.log_params({k: str(v)[:250] for k, v in params.items()})
            for k, v in metrics.items():
                if isinstance(v, (int, float)) and v == v:
                    mlflow.log_metric(k, float(v))
        payload["backend"] = "file+mlflow"
    except Exception:
        pass
    return payload
