"""Inference gateway: route → cache → generate → log (TTFT, cost, batch)."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from inference.router import generate, route
from inference import cache as resp_cache
from inference.queue import enqueue
from inference.retry import with_retry
from security.guardrails.scan import scan

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
            ttft_ms REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            tokens_per_sec REAL,
            cache_hit INTEGER,
            prompt_chars INTEGER,
            cost_usd REAL
        )
    """)
    con.execute("PRAGMA table_info(inference_log)")
    cols = {r[1] for r in con.execute("PRAGMA table_info(inference_log)").fetchall()}
    for col, ddl in {
        "ttft_ms": "ALTER TABLE inference_log ADD COLUMN ttft_ms REAL",
        "tokens_per_sec": "ALTER TABLE inference_log ADD COLUMN tokens_per_sec REAL",
        "cost_usd": "ALTER TABLE inference_log ADD COLUMN cost_usd REAL",
    }.items():
        if col not in cols:
            con.execute(ddl)
    con.commit()
    con.close()


def _cost(tokens_in: int, tokens_out: int) -> float:
    pin = float(os.getenv("NEXUS_USD_PER_1K_IN", "0") or 0)
    pout = float(os.getenv("NEXUS_USD_PER_1K_OUT", "0") or 0)
    return round((tokens_in / 1000.0) * pin + (tokens_out / 1000.0) * pout, 6)


def complete(prompt: str, force: str | None = None, use_cache: bool = True) -> dict:
    def _run():
        guard = scan(prompt, "prompt")
        if not guard["allowed"]:
            return {
                "text": "Blocked by guardrails.",
                "route": "blocked",
                "blocked": True,
                "findings": guard["findings"],
                "latency_ms": 0,
                "ttft_ms": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0,
            }
        _ensure_log()
        decision = route(prompt, force=force)
        if use_cache:
            hit = resp_cache.get(decision.label, prompt)
            if hit:
                _log(hit, prompt, cache_hit=1)
                return hit

        def _gen():
            return generate(prompt, force=force)

        def _fallback(err: Exception):
            mock = generate(prompt, force="mock")
            mock["fallback_from"] = decision.label
            mock["provider_error"] = str(err)
            return mock

        result = with_retry(_gen, retries=2, fallback=_fallback)
        result["cost_usd"] = _cost(int(result.get("tokens_in") or 0), int(result.get("tokens_out") or 0))
        if use_cache and not result.get("blocked"):
            resp_cache.put(decision.label, prompt, result)
        _log(result, prompt, cache_hit=0)
        return result

    return enqueue(_run)


def complete_batch(prompts: list[str], force: str | None = None, use_cache: bool = True) -> list[dict]:
    """Sequential batching (no continuous batching server in this repo)."""
    return [complete(p, force=force, use_cache=use_cache) for p in prompts]


def _log(result: dict, prompt: str, cache_hit: int):
    con = sqlite3.connect(LOG_DB)
    con.execute(
        """INSERT INTO inference_log
           (ts, route, latency_ms, ttft_ms, tokens_in, tokens_out, tokens_per_sec, cache_hit, prompt_chars, cost_usd)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            result.get("route"),
            result.get("latency_ms"),
            result.get("ttft_ms"),
            result.get("tokens_in"),
            result.get("tokens_out"),
            result.get("tokens_per_sec"),
            cache_hit,
            len(prompt),
            result.get("cost_usd") or 0,
        ),
    )
    con.commit()
    con.close()


def stats() -> dict:
    _ensure_log()
    con = sqlite3.connect(LOG_DB)
    rows = con.execute(
        """SELECT route, COUNT(*), ROUND(AVG(latency_ms),2), SUM(cache_hit),
                  SUM(tokens_in), SUM(tokens_out), ROUND(AVG(ttft_ms),2),
                  ROUND(AVG(tokens_per_sec),2), ROUND(SUM(cost_usd),6)
           FROM inference_log GROUP BY route"""
    ).fetchall()
    total = con.execute("SELECT COUNT(*) FROM inference_log").fetchone()[0]
    hits = con.execute("SELECT SUM(cache_hit) FROM inference_log").fetchone()[0] or 0
    con.close()
    return {
        "total_calls": total,
        "cache_hit_rate": round(hits / total, 4) if total else 0,
        "by_route": [
            {
                "route": r[0],
                "calls": r[1],
                "avg_latency_ms": r[2],
                "cache_hits": r[3],
                "tokens_in": r[4],
                "tokens_out": r[5],
                "avg_ttft_ms": r[6],
                "avg_tokens_per_sec": r[7],
                "cost_usd": r[8],
            }
            for r in rows
        ],
    }
