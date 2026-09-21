"""Kafka / Redpanda adapter. Idle unless KAFKA_BOOTSTRAP is set."""
from __future__ import annotations

import os


def status() -> dict:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP") or os.getenv("REDPANDA_BROKERS")
    if not bootstrap:
        return {
            "configured": False,
            "connected": False,
            "backend": "in_process_replay",
            "note": "KAFKA_BOOTSTRAP unset. Streaming uses in-process weekly replay.",
        }
    return {
        "configured": True,
        "connected": False,
        "backend": "in_process_replay",
        "note": f"Broker {bootstrap} is configured but this process does not start a consumer without an explicit worker.",
    }
