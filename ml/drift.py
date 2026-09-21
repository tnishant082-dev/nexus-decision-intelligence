"""Population Stability Index on numeric features vs a reference snapshot."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ml.paths import ROOT

OUT = ROOT / "ml" / "drift"


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    if len(expected) < 20 or len(actual) < 20:
        return float("nan")
    qs = np.linspace(0, 1, bins + 1)
    cuts = np.unique(np.quantile(expected, qs))
    if len(cuts) < 3:
        return 0.0
    e_counts, _ = np.histogram(expected, bins=cuts)
    a_counts, _ = np.histogram(actual, bins=cuts)
    e = e_counts / max(e_counts.sum(), 1)
    a = a_counts / max(a_counts.sum(), 1)
    e = np.clip(e, 1e-6, None)
    a = np.clip(a, 1e-6, None)
    return float(np.sum((a - e) * np.log(a / e)))


def run(current: pd.DataFrame, reference: pd.DataFrame, cols: list[str]) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cols:
        if c not in current.columns or c not in reference.columns:
            continue
        val = psi(reference[c].to_numpy(dtype=float), current[c].to_numpy(dtype=float))
        rows.append({"feature": c, "psi": None if val != val else round(val, 4), "flag": val > 0.2 if val == val else False})
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "PSI with quantile bins from reference",
        "threshold_note": "0.2 is a common heuristic, not a business SLA",
        "features": rows,
    }
    (OUT / "last_drift.json").write_text(json.dumps(report, indent=2))
    return report
