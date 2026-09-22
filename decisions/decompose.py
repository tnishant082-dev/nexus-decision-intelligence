"""Split a warehouse late-line pool into order volume and rate excess.

The dollars are an accounting identity on service-risk exposure. They are not
a causal effect of moving orders and they are not recovered EBITDA.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

DB = Path(__file__).resolve().parents[1] / "data-engineering" / "warehouse" / "nexus.duckdb"

# A residual below this share of the pool is size, not a worse late rate.
SMALL_RATE_EXCESS_SHARE = 0.10

FORMULA = (
    "late_line_revenue = volume_dollars + rate_excess_dollars, "
    "where volume_dollars = orders * rest_of_network_late_rate * (late_line_revenue / late_orders) "
    "and rate_excess_dollars = orders * (warehouse_late_rate - rest_of_network_late_rate) "
    "* (late_line_revenue / late_orders). "
    "This is an accounting split of the exposure pool, not a causal effect and not recovered EBITDA."
)

_ORDER_SQL = """
SELECT
  warehouse_name,
  COUNT(*)::INTEGER AS orders,
  COALESCE(SUM(is_late), 0)::INTEGER AS late_orders,
  COALESCE(SUM(late_line_revenue), 0) AS late_line_revenue
FROM (
  SELECT
    order_id,
    arg_max(warehouse_name, sales) AS warehouse_name,
    MAX(is_late)::INTEGER AS is_late,
    SUM(late_sales) AS late_line_revenue
  FROM (
    SELECT
      o.order_id,
      w.warehouse_name,
      CASE WHEN o.is_revenue = 1 THEN o.net_sales ELSE 0 END AS sales,
      CASE WHEN o.is_revenue = 1 AND o.is_late = 1 THEN o.net_sales ELSE 0 END AS late_sales,
      o.is_late::INTEGER AS is_late
    FROM fact_orders o
    JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
  )
  GROUP BY order_id
)
GROUP BY warehouse_name
"""


def exposure_split(db: Path | None = None, warehouse: str | None = None) -> dict[str, Any]:
    """Order-grain split of one warehouse's late-line revenue.

    The benchmark rate is the rest of the network, the same contrast as the
    warehouse study. ``volume_dollars`` is what this warehouse's orders would
    contribute if they were late at that rate, holding its own dollars per
    late order. ``rate_excess_dollars`` is the residual.
    """
    path = Path(db) if db is not None else DB
    if not path.exists():
        return _failed(f"warehouse missing at {path}")
    try:
        con = duckdb.connect(str(path), read_only=True)
        try:
            rows = con.execute(_ORDER_SQL).fetchall()
            columns = ["warehouse_name", "orders", "late_orders", "late_line_revenue"]
            pools = [dict(zip(columns, row)) for row in rows]
        finally:
            con.close()
    except Exception as exc:  # noqa: BLE001 — a missing table must not sink the decision
        return _failed(str(exc))
    if not pools:
        return _failed("no orders to split")

    named = str(warehouse) if warehouse else None
    if named is None:
        chosen = max(pools, key=lambda row: (float(row["late_line_revenue"]), str(row["warehouse_name"])))
        named = str(chosen["warehouse_name"])
    focal = next((row for row in pools if str(row["warehouse_name"]) == named), None)
    if focal is None:
        return _failed(f"warehouse not in the extract: {named}")

    others = [row for row in pools if str(row["warehouse_name"]) != named]
    orders = int(focal["orders"])
    late_orders = int(focal["late_orders"])
    late_raw = float(focal["late_line_revenue"] or 0)
    rest_orders = sum(int(row["orders"]) for row in others)
    rest_late_orders = sum(int(row["late_orders"]) for row in others)
    if orders <= 0:
        return _failed(f"{named} has no orders")
    if rest_orders <= 0:
        return _failed("rest of the network has no orders, so there is no benchmark late rate")

    warehouse_late_rate = late_orders / orders
    rest_late_rate = rest_late_orders / rest_orders
    if late_orders <= 0:
        volume_raw = 0.0
    else:
        dollars_per_late_order = late_raw / late_orders
        volume_raw = orders * rest_late_rate * dollars_per_late_order

    late = round(late_raw, 2)
    volume = round(volume_raw, 2)
    excess = round(late - volume, 2)
    share = (excess / late) if late else 0.0
    volume_share = (volume / late) if late else 0.0
    other_max = max((float(row["late_line_revenue"] or 0) for row in others), default=0.0)
    pool_is_large = late_raw > 0 and late_raw >= other_max
    share_is_small = abs(share) < SMALL_RATE_EXCESS_SHARE
    return {
        "ok": True,
        "grain": "order",
        "warehouse": named,
        "benchmark": "rest of the network",
        "late_line_revenue": late,
        "exposure": late,
        "means": "Sales dollars on late lines. Service-risk exposure.",
        "does_not_mean": "Lost sales, a causal effect, or recovered EBITDA.",
        "orders": orders,
        "late_orders": late_orders,
        "warehouse_late_rate": warehouse_late_rate,
        "rest_orders": rest_orders,
        "rest_late_orders": rest_late_orders,
        "rest_of_network_late_rate": rest_late_rate,
        "volume_dollars": volume,
        "rate_excess_dollars": excess,
        "volume_share": volume_share,
        "rate_excess_share": share,
        "rate_excess_share_is_small": share_is_small,
        "pool_is_large": pool_is_large,
        "formula": FORMULA,
        "explanation": _explanation(named, late, volume, excess, share, pool_is_large and share_is_small),
        "causal_claim": False,
    }


def _explanation(
    warehouse: str,
    late: float,
    volume: float,
    excess: float,
    share: float,
    volume_not_rate: bool,
) -> str:
    pool = _dollars(late)
    size = _dollars(volume)
    residual = _dollars(excess)
    if volume_not_rate:
        return (
            f"{warehouse} is large, not later: {size} of {pool} late-line exposure "
            f"is the order volume expected at the rest-of-network late rate, and {residual} is rate excess."
        )
    if share >= 0.5:
        return (
            f"{warehouse} is later, not only large: rate excess is {residual} of {pool} late-line exposure, "
            f"and {size} is the order volume expected at the rest-of-network late rate."
        )
    return (
        f"{warehouse} late-line exposure of {pool} splits into {size} of order volume "
        f"at the rest-of-network late rate and {residual} of rate excess."
    )


def _dollars(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def _failed(error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "formula": FORMULA,
        "causal_claim": False,
        "explanation": None,
    }
