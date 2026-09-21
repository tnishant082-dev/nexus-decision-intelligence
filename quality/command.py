"""Data quality command center over the extract snapshot."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "artifacts" / "quality_snapshot.json"


def load_report(path: Path | None = None) -> dict:
    return json.loads((path or SNAPSHOT).read_text())


def score(report: dict | None = None) -> dict:
    r = report or load_report()
    return {
        "score": r.get("score"),
        "checks_passed": r.get("checks_passed"),
        "checks_total": r.get("checks_total"),
        "incidents": r.get("incidents") or [],
        "freshness": r.get("freshness"),
        "schema_drift": r.get("schema_drift"),
        "note": "Score uses extract-end freshness, not wall-clock SLA. Lag vs today is expected on this historical extract.",
    }
