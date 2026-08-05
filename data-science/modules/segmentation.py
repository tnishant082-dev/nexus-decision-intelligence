
"""Customer RFM-ish segmentation for analytics (not full churn model)."""
from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
OUT = Path(__file__).resolve().parents[1] / "outputs"

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("""
        SELECT c.segment,
               COUNT(DISTINCT c.customer_key) AS customers,
               ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END)/1e6,2) AS revenue_m,
               ROUND(AVG(o.is_otif)*100,2) AS otif_pct,
               ROUND(AVG(o.is_late)*100,2) AS late_pct
        FROM dim_customer c
        JOIN fact_orders o ON c.customer_key = o.customer_key
        GROUP BY 1 ORDER BY revenue_m DESC
    """).df()
    con.close()
    out = {"by_segment": df.to_dict(orient="records")}
    (OUT / "segmentation.json").write_text(json.dumps(out, indent=2))
    return out

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
