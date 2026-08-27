"""Inference gateway: route → cache → generate → log."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from inference.router import generate, route
from inference import cache as resp_cache

LOG_DB = Path(__file__).resolve().parents[1] / "monitoring" / "inference_logs.sqlite"

def _ensure_log():
    LOG_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(LOG_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS inference_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            route TEXT,
            latency_ms REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            cache_hit INTEGER,
            prompt_chars INTEGER
        )
    """)
    con.commit()
    con.close()

def complete(prompt: str, force: str | None = None, use_cache: bool = True) -> dict:
    _ensure_log()
    decision = route(prompt, force=force)
    if use_cache:
        hit = resp_cache.get(decision.label, prompt)
        if hit:
            _log(hit, prompt, cache_hit=1)
            return hit
    result = generate(prompt, force=force)
    if use_cache:
        resp_cache.put(decision.label, prompt, result)
    _log(result, prompt, cache_hit=0)
    return result

def _log(result: dict, prompt: str, cache_hit: int):
    con = sqlite3.connect(LOG_DB)
    con.execute(
        "INSERT INTO inference_log (ts, route, latency_ms, tokens_in, tokens_out, cache_hit, prompt_chars) VALUES (?,?,?,?,?,?,?)",
        (
            datetime.now(timezone.utc).isoformat(),
            result.get("route"),
            result.get("latency_ms"),
            result.get("tokens_in"),
            result.get("tokens_out"),
            cache_hit,
            len(prompt),
        ),
    )
    con.commit()
    con.close()

def stats() -> dict:
    _ensure_log()
    con = sqlite3.connect(LOG_DB)
    rows = con.execute(
        "SELECT route, COUNT(*), ROUND(AVG(latency_ms),2), SUM(cache_hit), SUM(tokens_in), SUM(tokens_out) FROM inference_log GROUP BY route"
    ).fetchall()
    total = con.execute("SELECT COUNT(*) FROM inference_log").fetchone()[0]
    con.close()
    return {
        "total_calls": total,
        "by_route": [
            {"route": r[0], "calls": r[1], "avg_latency_ms": r[2], "cache_hits": r[3],
             "tokens_in": r[4], "tokens_out": r[5]}
            for r in rows
        ],
    }
