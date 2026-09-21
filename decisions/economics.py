"""Dollarize service, logistics, inventory, and customer risk on the local extract.

These are **accounting identities and documented proxies**, not causal P&L.
Late revenue is sales that shipped late — not automatically lost sales.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb

DB = Path(__file__).resolve().parents[1] / "data-engineering" / "warehouse" / "nexus.duckdb"
SAMPLE_OTIF_TARGET = 92.0  # docs/knowledge/01_otif_policy.md Enterprise SAMPLE target


def _con(db: Path = DB):
    return duckdb.connect(str(db), read_only=True)


def value_at_stake(db: Path = DB) -> dict:
    con = _con(db)
    rev, late_rev, profit, late_profit = con.execute(
        """
        SELECT
          SUM(CASE WHEN is_revenue=1 THEN net_sales ELSE 0 END),
          SUM(CASE WHEN is_revenue=1 AND is_late=1 THEN net_sales ELSE 0 END),
          SUM(CASE WHEN is_revenue=1 THEN line_profit ELSE 0 END),
          SUM(CASE WHEN is_revenue=1 AND is_late=1 THEN line_profit ELSE 0 END)
        FROM fact_orders
        """
    ).fetchone()
    otif = con.execute(
        """
        SELECT 100.0 * AVG(otif) FROM (
          SELECT MIN(is_otif) AS otif FROM fact_orders GROUP BY order_id
        )
        """
    ).fetchone()[0]
    freight, delay_cost, expedite = con.execute(
        """
        SELECT SUM(freight_cost), SUM(delay_cost),
               SUM(CASE WHEN is_advance=1 THEN freight_cost ELSE 0 END)
        FROM fact_shipments
        """
    ).fetchone()
    unfilled = con.execute("SELECT SUM(unfilled_value) FROM fact_inventory").fetchone()[0]
    churn = con.execute("SELECT customers, avg_ltv, churn_proxy_180d_pct FROM v_customer_kpis").fetchone()
    growth = con.execute("SELECT year, revenue_m FROM v_finance_growth ORDER BY year").df()
    con.close()
    customers, avg_ltv, churn_pct = churn
    ltv_at_risk = (customers or 0) * (avg_ltv or 0) * ((churn_pct or 0) / 100.0)
    yoy = None
    if len(growth) >= 2:
        # full years 2016 vs 2017 in this extract (2018 is a stub month)
        g = {int(r.year): float(r.revenue_m) for r in growth.itertuples()}
        if 2016 in g and 2017 in g:
            yoy = {
                "from_year": 2016,
                "to_year": 2017,
                "revenue_from_m": g[2016],
                "revenue_to_m": g[2017],
                "delta_m": round(g[2017] - g[2016], 2),
                "note": "2018 is a partial month in the extract and is excluded from this YoY pair.",
            }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_otif_target_pct": SAMPLE_OTIF_TARGET,
        "actual_otif_pct": round(float(otif or 0), 2),
        "otif_gap_pp": round(SAMPLE_OTIF_TARGET - float(otif or 0), 2),
        "revenue": round(float(rev or 0), 2),
        "late_revenue": round(float(late_rev or 0), 2),
        "late_revenue_share_pct": round(100.0 * float(late_rev or 0) / float(rev or 1), 2),
        "late_profit": round(float(late_profit or 0), 2),
        "profit": round(float(profit or 0), 2),
        "freight": round(float(freight or 0), 2),
        "delay_cost": round(float(delay_cost or 0), 2),
        "expedite_freight": round(float(expedite or 0), 2),
        "unfilled_value_all_snapshots": round(float(unfilled or 0), 2),
        "churn_proxy_customers_pct": churn_pct,
        "churn_ltv_at_risk_proxy": round(float(ltv_at_risk), 2),
        "yoy_2016_2017": yoy,
        "interpretation": {
            "late_revenue": "Revenue on late lines — service-risk exposure, not proven lost sales.",
            "delay_cost": "Modeled delay_cost on fact_shipments (extract field).",
            "expedite_freight": "Freight on is_advance=1 shipments (reactive air/expedite proxy).",
            "unfilled_value": "Sum of unfilled_value across inventory snapshots — not a single-day shortage P&L.",
            "churn_ltv": "customers × avg_ltv × 180d inactivity rate — inactivity proxy, not contracted churn.",
        },
    }


def warehouse_exceptions(db: Path = DB, limit: int = 12) -> list[dict]:
    con = _con(db)
    df = con.execute(
        """
        SELECT w.warehouse_name,
               ROUND(SUM(CASE WHEN o.is_revenue=1 AND o.is_late=1 THEN o.net_sales ELSE 0 END), 2) AS late_revenue,
               ROUND(AVG(o.is_late)*100, 2) AS late_pct,
               ROUND(AVG(o.is_otif)*100, 2) AS otif_pct,
               COUNT(DISTINCT o.order_id) AS orders
        FROM fact_orders o
        JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
        GROUP BY 1
        ORDER BY late_revenue DESC
        LIMIT ?
        """,
        [limit],
    ).df()
    con.close()
    out = []
    for r in df.to_dict(orient="records"):
        out.append({
            **r,
            "exception_type": "late_service",
            "owner": "Warehouse ops",
            "policy": "SAMPLE OTIF enterprise target 92% (docs/knowledge/01_otif_policy.md)",
            "action": "Split late vs short-ship; inspect top carriers feeding this node.",
        })
    return out


def carrier_exceptions(db: Path = DB, limit: int = 8) -> list[dict]:
    con = _con(db)
    df = con.execute(
        """
        SELECT c.carrier_name,
               ROUND(SUM(s.delay_cost), 2) AS delay_cost,
               ROUND(SUM(s.freight_cost), 2) AS freight,
               ROUND(AVG(s.is_late)*100, 2) AS late_pct,
               COUNT(*) AS shipments
        FROM fact_shipments s
        JOIN dim_carrier c ON s.carrier_key = c.carrier_key
        GROUP BY 1
        ORDER BY delay_cost DESC
        LIMIT ?
        """,
        [limit],
    ).df()
    con.close()
    return [{**r, "exception_type": "carrier_delay", "owner": "Transportation",
             "policy": "SAMPLE freight expedite playbook (docs/knowledge/04_freight_expedite.md)",
             "action": "Cap expedite share; renegotiate lanes with highest delay_cost."}
            for r in df.to_dict(orient="records")]
