"""Linear what-if sensitivities — not a digital twin."""
from __future__ import annotations

from pathlib import Path

import duckdb

from decisions.economics import DB, SAMPLE_OTIF_TARGET


def close_late_gap(warehouse_name: str | None = None, close_pct: float = 0.25, db: Path = DB) -> dict:
    """If `close_pct` of late revenue at a node (or network) became on-time, report the $ pool.

    This does **not** simulate demand response. It sizes the service-risk pool you would be working.
    """
    close_pct = min(max(float(close_pct), 0.0), 1.0)
    con = duckdb.connect(str(db), read_only=True)
    if warehouse_name:
        row = con.execute(
            """
            SELECT w.warehouse_name,
                   SUM(CASE WHEN o.is_revenue=1 AND o.is_late=1 THEN o.net_sales ELSE 0 END) AS late_revenue,
                   AVG(o.is_late) AS late_rate
            FROM fact_orders o
            JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
            WHERE w.warehouse_name = ?
            GROUP BY 1
            """,
            [warehouse_name],
        ).fetchone()
        label = warehouse_name
    else:
        row = con.execute(
            """
            SELECT 'NETWORK',
                   SUM(CASE WHEN is_revenue=1 AND is_late=1 THEN net_sales ELSE 0 END),
                   AVG(is_late)
            FROM fact_orders
            """
        ).fetchone()
        label = "NETWORK"
    con.close()
    if not row:
        return {"ok": False, "error": "warehouse not found"}
    late = float(row[1] or 0)
    return {
        "ok": True,
        "scope": label,
        "late_revenue_pool": round(late, 2),
        "close_pct": close_pct,
        "service_risk_addressed": round(late * close_pct, 2),
        "method": "linear scale of late-line net_sales",
        "limitations": [
            "Does not forecast recovered demand or penalty clauses",
            "Closing late does not automatically convert to OTIF (in-full still required)",
            f"SAMPLE enterprise OTIF target remains {SAMPLE_OTIF_TARGET}%",
        ],
    }


def cut_expedite(cut_pct: float = 0.30, db: Path = DB) -> dict:
    cut_pct = min(max(float(cut_pct), 0.0), 1.0)
    con = duckdb.connect(str(db), read_only=True)
    exp = con.execute(
        "SELECT SUM(CASE WHEN is_advance=1 THEN freight_cost ELSE 0 END) FROM fact_shipments"
    ).fetchone()[0]
    con.close()
    pool = float(exp or 0)
    return {
        "ok": True,
        "expedite_freight_pool": round(pool, 2),
        "cut_pct": cut_pct,
        "freight_at_stake": round(pool * cut_pct, 2),
        "method": "linear cut of is_advance freight_cost",
        "limitations": ["May worsen OTIF if expedite was covering poor planning — pair with warehouse late_pct"],
    }


def list_warehouses(db: Path = DB) -> list[str]:
    con = duckdb.connect(str(db), read_only=True)
    names = [r[0] for r in con.execute(
        "SELECT warehouse_name FROM dim_warehouse ORDER BY 1"
    ).fetchall()]
    con.close()
    return names
