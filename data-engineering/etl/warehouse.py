"""Load cleaned parquet into DuckDB warehouse with KPI views."""
from __future__ import annotations

import hashlib
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
  ROUND(
    100.0 * SUM(CASE WHEN is_revenue=1 THEN line_profit ELSE 0 END)
    / NULLIF(SUM(CASE WHEN is_revenue=1 THEN net_sales ELSE 0 END), 0)
  , 2) AS margin_pct,
  COUNT(DISTINCT CASE WHEN is_revenue=1 THEN order_id END) AS orders,
  ROUND(AVG(CASE WHEN is_revenue=1 THEN is_otif END)*100, 2) AS otif_line_pct
FROM fact_orders;

CREATE OR REPLACE VIEW v_finance_growth AS
SELECT
  d.calendar_year AS year,
  ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END)/1e6, 2) AS revenue_m,
  ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.line_profit ELSE 0 END)/1e6, 2) AS profit_m,
  COUNT(DISTINCT CASE WHEN o.is_revenue=1 THEN o.order_id END) AS orders
FROM fact_orders o
JOIN dim_date d ON o.order_date_key = d.date_key
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE VIEW v_otif_order AS
SELECT
  ROUND(AVG(otif)*100, 2) AS otif_pct,
  ROUND(AVG(perfect)*100, 2) AS perfect_order_pct
FROM (
  SELECT order_id, MIN(is_otif) AS otif, MIN(is_perfect_order) AS perfect
  FROM fact_orders GROUP BY order_id
);

CREATE OR REPLACE VIEW v_fill_rate AS
SELECT
  ROUND(AVG(is_in_full)*100, 2) AS fill_rate_pct,
  ROUND(AVG(is_otif)*100, 2) AS shipment_otif_pct,
  COUNT(*) AS shipments
FROM fact_shipments;

CREATE OR REPLACE VIEW v_logistics AS
SELECT
  ROUND(SUM(freight_cost)/1e6, 2) AS freight_m,
  ROUND(AVG(freight_cost), 2) AS cost_per_ship,
  ROUND(AVG(is_late)*100, 2) AS delay_rate_pct,
  ROUND(SUM(co2_kg)/1000, 1) AS co2_tonnes,
  COUNT(*) AS shipments
FROM fact_shipments;

CREATE OR REPLACE VIEW v_inventory_kpis AS
SELECT
  ROUND(AVG(stockout_flag)*100, 2) AS stockout_pct,
  ROUND(AVG(CASE WHEN demand_units > 0 THEN on_hand_units / demand_units END), 2) AS coverage_ratio,
  ROUND(SUM(issues_units) / NULLIF(AVG(on_hand_units), 0), 4) AS turns_proxy,
  ROUND(SUM(on_hand_value)/1e6, 2) AS on_hand_value_m_all_snapshots,
  COUNT(*) AS snapshot_rows
FROM fact_inventory;

CREATE OR REPLACE VIEW v_inventory_latest AS
SELECT
  i.date_key,
  ROUND(SUM(i.on_hand_value)/1e6, 2) AS on_hand_m,
  ROUND(SUM(i.on_hand_units), 0) AS on_hand_units,
  ROUND(AVG(i.stockout_flag)*100, 2) AS stockout_pct
FROM fact_inventory i
WHERE i.date_key = (SELECT MAX(date_key) FROM fact_inventory)
GROUP BY 1;

CREATE OR REPLACE VIEW v_stockout_risk AS
SELECT
  p.product_key,
  p.product_name,
  p.category_name,
  p.abc_class,
  ROUND(AVG(i.stockout_flag)*100, 2) AS stockout_pct,
  ROUND(AVG(CASE WHEN i.demand_units > 0 THEN i.on_hand_units / i.demand_units END), 3) AS coverage_ratio,
  ROUND(SUM(i.unfilled_units), 1) AS unfilled_units
FROM fact_inventory i
JOIN dim_product p ON i.product_key = p.product_key
GROUP BY 1,2,3,4
ORDER BY stockout_pct DESC, unfilled_units DESC;

CREATE OR REPLACE VIEW v_customer_ltv AS
SELECT
  c.customer_key,
  c.segment,
  COUNT(DISTINCT o.order_id) AS frequency,
  ROUND(SUM(CASE WHEN o.is_revenue=1 THEN o.net_sales ELSE 0 END), 2) AS monetary,
  MIN(d.date)::DATE AS first_order,
  MAX(d.date)::DATE AS last_order
FROM dim_customer c
JOIN fact_orders o ON c.customer_key = o.customer_key
JOIN dim_date d ON o.order_date_key = d.date_key
GROUP BY 1, 2;

CREATE OR REPLACE VIEW v_customer_kpis AS
WITH bounds AS (
  SELECT MAX(d.date)::DATE AS asof
  FROM fact_orders o JOIN dim_date d ON o.order_date_key = d.date_key
),
base AS (
  SELECT v.*, b.asof,
         datediff('day', v.last_order, b.asof) AS recency_days
  FROM v_customer_ltv v CROSS JOIN bounds b
)
SELECT
  COUNT(*) AS customers,
  ROUND(AVG(monetary), 2) AS avg_ltv,
  ROUND(100.0 * AVG(CASE WHEN recency_days <= 90 THEN 1 ELSE 0 END), 2) AS retained_90d_pct,
  ROUND(100.0 * AVG(CASE WHEN recency_days > 180 THEN 1 ELSE 0 END), 2) AS churn_proxy_180d_pct
FROM base;

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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_warehouse(
    cleaned: Path = CLEANED,
    db_path: Path = DB_PATH,
    incremental: bool = True,
) -> dict:
    WAREHOUSE.mkdir(parents=True, exist_ok=True)
    meta_path = WAREHOUSE / "warehouse_meta.json"
    prev = {}
    if meta_path.exists():
        try:
            prev = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            prev = {}
    prev_hashes = {t["table"]: t.get("sha256") for t in prev.get("tables", [])}

    hashes = {}
    for name in TABLES:
        pq = cleaned / f"{name}.parquet"
        if pq.exists():
            hashes[name] = _sha256(pq)

    db_exists = db_path.exists()
    if not incremental and db_exists:
        db_path.unlink()
        db_exists = False

    con = duckdb.connect(str(db_path))
    loaded = []
    existing_tables = set()
    if db_exists:
        existing_tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}

    use_incremental = incremental and db_exists and prev_hashes
    mode = "incremental" if use_incremental else "full"
    for name, digest in hashes.items():
        pq = cleaned / f"{name}.parquet"
        skip = (
            use_incremental
            and prev_hashes.get(name) == digest
            and name in existing_tables
        )
        if skip:
            n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            loaded.append({"table": name, "rows": n, "sha256": digest, "skipped": True})
            continue
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{pq.as_posix()}')")
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        loaded.append({"table": name, "rows": n, "sha256": digest, "skipped": False})

    con.execute(KPI_VIEWS_SQL)
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "load_mode": mode,
        "tables": loaded,
        "engine": "duckdb",
        "incremental": incremental,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    con.close()
    return meta


if __name__ == "__main__":
    print(json.dumps(load_warehouse(), indent=2))
