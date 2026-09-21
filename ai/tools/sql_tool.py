"""Read-only SQL tool against DuckDB warehouse (SELECT only)."""
from __future__ import annotations
import re
from pathlib import Path
import duckdb

DB = Path(__file__).resolve().parents[2] / "data-engineering" / "warehouse" / "nexus.duckdb"

FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|COPY|CREATE|REPLACE|GRANT|PRAGMA)\b", re.I)

def run_sql(sql: str, limit: int = 50) -> dict:
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        return {"ok": False, "error": "Only read-only SELECT queries are allowed."}
    if not re.match(r"^SELECT\b|^WITH\b", sql, re.I):
        return {"ok": False, "error": "Query must start with SELECT or WITH."}
    wrapped = f"SELECT * FROM ({sql}) AS q LIMIT {int(limit)}"
    try:
        con = duckdb.connect(str(DB), read_only=True)
        df = con.execute(wrapped).df()
        con.close()
        return {"ok": True, "sql": sql, "rows": df.to_dict(orient="records"), "columns": list(df.columns)}
    except Exception as e:
        return {"ok": False, "error": str(e), "sql": sql}

# Curated KPI snippets used by the investigate agent
KPI_SNIPPETS = {
    "otif": """
        SELECT ROUND(AVG(otif)*100,2) AS otif_pct, ROUND(AVG(perfect)*100,2) AS perfect_order_pct
        FROM (
          SELECT order_id, MIN(is_otif) AS otif, MIN(is_perfect_order) AS perfect
          FROM fact_orders GROUP BY order_id
        )
    """,
    "late_by_warehouse": """
        SELECT w.warehouse_name, ROUND(AVG(o.is_late)*100,2) AS late_pct,
               ROUND(AVG(o.is_otif)*100,2) AS otif_pct, COUNT(*) AS lines
        FROM fact_orders o
        JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
        GROUP BY 1 ORDER BY late_pct DESC
    """,
    "late_by_carrier": """
        SELECT c.carrier_name, ROUND(AVG(s.is_late)*100,2) AS late_pct,
               COUNT(*) AS shipments, ROUND(SUM(s.freight_cost),0) AS freight
        FROM fact_shipments s
        JOIN dim_carrier c ON s.carrier_key = c.carrier_key
        GROUP BY 1 ORDER BY late_pct DESC
    """,
    "exec_kpis": "SELECT * FROM v_exec_kpis",
    "logistics": "SELECT * FROM v_logistics",
    "fill_rate": "SELECT * FROM v_fill_rate",
    "customer_kpis": "SELECT * FROM v_customer_kpis",
    "inventory_coverage": """
        SELECT ROUND(SUM(on_hand_value)/1e6,2) AS on_hand_value_m_all_snapshots,
               ROUND(AVG(stockout_flag)*100,2) AS stockout_pct
        FROM fact_inventory
    """,
    "category_revenue": """
        SELECT p.category_name, ROUND(SUM(o.net_sales)/1e6,2) AS revenue_m,
               ROUND(AVG(o.is_otif)*100,2) AS otif_pct
        FROM fact_orders o
        JOIN dim_product p ON o.product_key = p.product_key
        WHERE o.is_revenue = 1
        GROUP BY 1 ORDER BY revenue_m DESC LIMIT 15
    """,
    "late_revenue": """
        SELECT ROUND(SUM(CASE WHEN is_revenue=1 AND is_late=1 THEN net_sales ELSE 0 END)/1e6,2) AS late_revenue_m,
               ROUND(100.0 * SUM(CASE WHEN is_revenue=1 AND is_late=1 THEN net_sales ELSE 0 END)
                     / NULLIF(SUM(CASE WHEN is_revenue=1 THEN net_sales ELSE 0 END),0), 2) AS late_share_pct
        FROM fact_orders
    """,
}
