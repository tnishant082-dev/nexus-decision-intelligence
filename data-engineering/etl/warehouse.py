"""Load cleaned parquet into DuckDB warehouse with views for analytics/ML."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
CLEANED = ROOT / "cleaned"
WAREHOUSE = ROOT / "warehouse"
DB_PATH = WAREHOUSE / "nexus.duckdb"

TABLES = [
    "dim_carrier", "dim_customer", "dim_date", "dim_delivery_status",
    "dim_order_status", "dim_payment_type", "dim_product", "dim_region",
    "dim_source_system", "dim_transport_mode", "dim_vendor", "dim_warehouse",
    "fact_inventory", "fact_orders", "fact_procurement", "fact_returns",
    "fact_shipments", "fact_vendor_performance",
    "ref_emission_factor", "ref_freight_tariff", "ref_lane_distance",
    "rls_user_map", "last_refresh",
]

KPI_VIEWS_SQL = """
CREATE OR REPLACE VIEW v_exec_kpis AS
SELECT
  ROUND(SUM(CASE WHEN is_revenue=1 THEN net_sales ELSE 0 END)/1e6, 2) AS revenue_m,
  ROUND(SUM(CASE WHEN is_revenue=1 THEN line_profit ELSE 0 END)/1e6, 2) AS profit_m,
  COUNT(DISTINCT CASE WHEN is_revenue=1 THEN order_id END) AS orders,
  ROUND(AVG(CASE WHEN is_revenue=1 THEN is_otif END)*100, 2) AS otif_line_pct
FROM fact_orders;

CREATE OR REPLACE VIEW v_otif_order AS
SELECT
  ROUND(AVG(otif)*100, 2) AS otif_pct,
  ROUND(AVG(perfect)*100, 2) AS perfect_order_pct
FROM (
  SELECT order_id, MIN(is_otif) AS otif, MIN(is_perfect_order) AS perfect
  FROM fact_orders GROUP BY order_id
);

CREATE OR REPLACE VIEW v_logistics AS
SELECT
  ROUND(SUM(freight_cost)/1e6, 2) AS freight_m,
  ROUND(AVG(freight_cost), 2) AS cost_per_ship,
  ROUND(AVG(is_late)*100, 2) AS delay_rate_pct,
  ROUND(SUM(co2_kg)/1000, 1) AS co2_tonnes,
  COUNT(*) AS shipments
FROM fact_shipments;

CREATE OR REPLACE VIEW v_demand_weekly AS
SELECT
  d.iso_year,
  d.week_of_year,
  d.week_start_date,
  p.category_name,
  o.warehouse_key,
  SUM(o.quantity) AS units,
  SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END) AS revenue,
  COUNT(DISTINCT o.order_id) AS orders
FROM fact_orders o
JOIN dim_date d ON o.order_date_key = d.date_key
JOIN dim_product p ON o.product_key = p.product_key
GROUP BY 1,2,3,4,5;
"""

def load_warehouse(cleaned: Path = CLEANED, db_path: Path = DB_PATH) -> dict:
    WAREHOUSE.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    loaded = []
    for name in TABLES:
        pq = cleaned / f"{name}.parquet"
        if not pq.exists():
            continue
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{pq.as_posix()}')")
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        loaded.append({"table": name, "rows": n})
    con.execute(KPI_VIEWS_SQL)
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "tables": loaded,
        "engine": "duckdb",
    }
    (WAREHOUSE / "warehouse_meta.json").write_text(json.dumps(meta, indent=2))
    con.close()
    return meta

if __name__ == "__main__":
    print(json.dumps(load_warehouse(), indent=2))
