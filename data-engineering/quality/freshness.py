"""Data freshness against dim_date (historical extract — lag can be years)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "nexus.duckdb"
CONTRACTS = ROOT / "contracts"
OUT = ROOT / "quality" / "freshness_report.json"


def freshness(db_path: Path = DB) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    today = datetime.now(timezone.utc).date()
    items = []
    for path in sorted(CONTRACTS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        fr = spec.get("freshness") or {}
        table = spec.get("table")
        col = fr.get("date_column")
        if not table or not col:
            continue
        existing = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if table not in existing:
            items.append({"table": table, "ok": False, "error": "missing table"})
            continue
        cal = fr.get("calendar_table")
        if cal:
            sql = f"""
                SELECT MAX(c.{fr['calendar_date']})::DATE
                FROM {table} t
                JOIN {cal} c ON t.{col} = c.{fr['calendar_key']}
            """
            max_d = con.execute(sql).fetchone()[0]
        else:
            max_d = con.execute(f"SELECT MAX({col})::DATE FROM {table}").fetchone()[0]
        lag = (today - max_d).days if max_d is not None else None
        max_lag = int(fr.get("max_lag_days", 4000))
        items.append({
            "table": table,
            "max_event_date": str(max_d) if max_d else None,
            "lag_days_vs_utc_today": lag,
            "threshold_days": max_lag,
            "passed": lag is not None and lag <= max_lag,
            "note": "Extract window ends 2018; lag vs today is expected for this portfolio dataset.",
        })
    con.close()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of_utc": today.isoformat(),
        "tables": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(freshness(), indent=2))
