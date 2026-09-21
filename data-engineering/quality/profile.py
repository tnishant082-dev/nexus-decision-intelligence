"""Column profiling for warehouse tables (nulls, distinct, numeric ranges)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "nexus.duckdb"
OUT = ROOT / "quality" / "profile_report.json"

PROFILE_TABLES = [
    "fact_orders",
    "fact_shipments",
    "fact_inventory",
    "dim_customer",
    "dim_product",
]


def profile(db_path: Path = DB) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    tables = []
    existing = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    for name in PROFILE_TABLES:
        if name not in existing:
            continue
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        col_meta = con.execute(f"DESCRIBE {name}").fetchall()
        columns = []
        for col, dtype, *_ in col_meta:
            nulls = con.execute(f"SELECT COUNT(*) FROM {name} WHERE {col} IS NULL").fetchone()[0]
            distinct = con.execute(f"SELECT COUNT(DISTINCT {col}) FROM {name}").fetchone()[0]
            entry = {
                "name": col,
                "dtype": str(dtype),
                "nulls": int(nulls),
                "null_pct": round(100.0 * nulls / n, 4) if n else None,
                "distinct": int(distinct),
            }
            if any(tok in str(dtype).upper() for tok in ("INT", "DOUBLE", "FLOAT", "DECIMAL", "HUGE")):
                mn, mx, avg = con.execute(
                    f"SELECT MIN({col}), MAX({col}), AVG({col}::DOUBLE) FROM {name}"
                ).fetchone()
                entry["min"] = mn
                entry["max"] = mx
                entry["avg"] = float(avg) if avg is not None else None
            columns.append(entry)
        tables.append({"table": name, "rows": int(n), "columns": columns})
    con.close()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "duckdb",
        "tables": tables,
        "note": "Descriptive profile of the local extract — not a production DQ SLA.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    md = ROOT / "quality" / "profile_report.md"
    lines = ["# Warehouse profile", "", f"Generated `{report['generated_at']}`", ""]
    for t in tables:
        lines.append(f"## {t['table']} ({t['rows']} rows)")
        lines.append("")
        lines.append("| column | dtype | nulls | distinct |")
        lines.append("|---|---|---|---|")
        for c in t["columns"]:
            lines.append(f"| `{c['name']}` | {c['dtype']} | {c['nulls']} | {c['distinct']} |")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = profile()
    print(f"profiled {len(r['tables'])} tables")
