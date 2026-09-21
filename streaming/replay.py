"""In-process weekly replay of the extract. Not Kafka, not live OMS CDC."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KPI = ROOT / "artifacts" / "kpi_snapshot.json"


def replay_extract(path: Path | None = None) -> list[dict]:
    data = json.loads((path or KPI).read_text())
    events = []
    for w in data.get("weekly") or []:
        anomaly = w["otif_pct"] < 32 or (w["late_revenue"] / max(w["revenue"], 1) > 0.7)
        events.append(
            {
                "ts": w["week"],
                "kind": "anomaly" if anomaly else "order_week",
                "revenue": w["revenue"],
                "late_revenue": w["late_revenue"],
                "otif_pct": w["otif_pct"],
                "orders": w["orders"],
                "anomaly": anomaly,
                "note": (
                    "Anomaly flag: OTIF < 32% or late share > 70% on this week of the extract."
                    if anomaly
                    else "Replay tick from fact_orders week grain."
                ),
            }
        )
    return events


def stream_stats(events: list[dict] | None = None) -> dict:
    events = events if events is not None else replay_extract()
    anomalies = [e for e in events if e.get("anomaly")]
    return {
        "ticks": len(events),
        "anomalies": len(anomalies),
        "anomaly_rate": round(1000 * len(anomalies) / len(events), 1) / 10 if events else 0,
        "backend": "in_process_replay",
        "kafka": False,
        "note": "In-process replay of the 2015–2018 week series. Kafka/Redpanda adapter stays idle unless you run a broker.",
    }
