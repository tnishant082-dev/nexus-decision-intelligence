"""Pearson correlations on numeric order flags/measures."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
OUT = Path(__file__).resolve().parents[1] / "outputs"


def run(db: Path = DB) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=True)
    row = con.execute("""
        SELECT
          corr(is_late::DOUBLE, days_ship_real::DOUBLE) AS corr_late_days,
          corr(is_otif::DOUBLE, line_profit::DOUBLE) AS corr_otif_profit,
          corr(is_late::DOUBLE, discount_rate::DOUBLE) AS corr_late_discount,
          corr(is_perfect_order::DOUBLE, is_otif::DOUBLE) AS corr_perfect_otif
        FROM fact_orders
        WHERE is_revenue = 1
    """).fetchone()
    n = con.execute("SELECT COUNT(*) FROM fact_orders WHERE is_revenue=1").fetchone()[0]
    con.close()
    report = {
        "methodology": "DuckDB corr() = Pearson product-moment on revenue lines",
        "n": int(n),
        "correlations": {
            "late_vs_days_ship": row[0],
            "otif_vs_profit": row[1],
            "late_vs_discount": row[2],
            "perfect_vs_otif": row[3],
        },
        "assumptions": ["Linear association", "No sampling weights"],
        "limitations": ["Correlation is not causation", "Flags are binary so bounds are limited"],
    }
    (OUT / "correlation.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
