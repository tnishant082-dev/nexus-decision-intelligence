"""In-process observability snapshot. Prometheus/Grafana stay optional."""
from __future__ import annotations

from evaluation.runner import run_evaluation
from inference.gateway import stats as inference_stats
from quality.command import score as quality_score
from simulation.engine import usage as sim_usage
from streaming.kafka_adapter import status as kafka_status
from streaming.replay import stream_stats
from ai.graphrag.neo4j_adapter import status as neo4j_status


def snapshot() -> dict:
    q = quality_score()
    stream = stream_stats()
    inf = inference_stats()
    ev = run_evaluation()
    return {
        "pipeline": {
            "quality_score": q["score"],
            "checks_passed": q["checks_passed"],
            "checks_total": q["checks_total"],
            "incidents": len(q["incidents"]),
            "note": q["note"],
        },
        "streaming": {
            "backend": stream["backend"],
            "kafka": stream["kafka"],
            "ticks": stream["ticks"],
            "anomalies": stream["anomalies"],
            "adapter": kafka_status(),
        },
        "graph": neo4j_status(),
        "inference": {
            "calls": inf.get("total_calls", 0),
            "cache_hit_rate": inf.get("cache_hit_rate", 0),
            "by_route": inf.get("by_route", []),
        },
        "agents": ev["summary"],
        "simulation": sim_usage(),
        "note": (
            "Collected in-process. Grafana JSON and prometheus.yml are examples — this function "
            "does not scrape a live Prometheus."
        ),
    }
