"""Local mock benchmark suite — writes results to monitoring tables. No GPU claims."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from inference.gateway import complete

OUT_DB = Path(__file__).resolve().parents[2] / "monitoring" / "inference_logs.sqlite"
PROMPTS = [
    ("short", "What is OTIF?"),
    ("medium", "Explain drivers of late deliveries across warehouses and carriers with recommended actions for ops leads. " * 3),
    ("long", "Provide a detailed multi-step investigation plan for declining OTIF, including SQL checks, inventory coverage, vendor SLA, freight expedite policy, and forecast implications. " * 8),
]

def run():
    results = []
    for name, prompt in PROMPTS:
        for force in ("mock", "small", "large"):
            r = complete(prompt, force=force, use_cache=False)
            results.append({"case": name, **{k: r[k] for k in ("route", "latency_ms", "tokens_in", "tokens_out", "hardware")}})
    OUT_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(OUT_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            case_name TEXT,
            route TEXT,
            latency_ms REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            hardware TEXT
        )
    """)
    ts = datetime.now(timezone.utc).isoformat()
    for row in results:
        con.execute(
            "INSERT INTO benchmark_results (ts, case_name, route, latency_ms, tokens_in, tokens_out, hardware) VALUES (?,?,?,?,?,?,?)",
            (ts, row["case"], row["route"], row["latency_ms"], row["tokens_in"], row["tokens_out"], row["hardware"]),
        )
    con.commit()
    con.close()
    summary = {
        "ran_at": ts,
        "n": len(results),
        "results": results,
        "disclaimer": "Local CPU mock timings only — not GPU throughput benchmarks.",
    }
    out = Path(__file__).resolve().parent / "last_bench.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run()
