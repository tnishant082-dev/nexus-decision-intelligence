"""Root-cause style breakdowns (associative, not causal)."""
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
    by_wh = con.execute("""
        SELECT w.warehouse_name,
               ROUND(AVG(o.is_late)*100, 2) AS late_pct,
               ROUND(AVG(o.is_otif)*100, 2) AS otif_pct,
               COUNT(*) AS lines,
               ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END)/1e6, 2) AS revenue_m
        FROM fact_orders o
        JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
        GROUP BY 1
        ORDER BY late_pct DESC
    """).df()
    by_cat = con.execute("""
        SELECT p.category_name,
               ROUND(AVG(o.is_otif)*100, 2) AS otif_pct,
               ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END)/1e6, 2) AS revenue_m,
               COUNT(*) AS lines
        FROM fact_orders o
        JOIN dim_product p ON o.product_key = p.product_key
        GROUP BY 1
        ORDER BY revenue_m DESC
    """).df()
    con.close()
    report = {
        "question": "Where is late/OTIF concentrated?",
        "methodology": "Group-by rates on fact_orders; no causal identification strategy.",
        "assumptions": ["Flags are correctly modeled in the extract", "Line grain is comparable across warehouses"],
        "limitations": ["Confounding by mix, season, and carrier is not controlled"],
        "late_by_warehouse": by_wh.to_dict(orient="records"),
        "otif_by_category": by_cat.to_dict(orient="records"),
    }
    (OUT / "rca.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2)[:1500])
