"""Linear SAMPLE what-if on extract KPIs. Not a network digital twin."""
from __future__ import annotations

from copy import deepcopy

SAMPLE_ELASTICITIES = {
    "inventory_otif_pp_per_pct": 0.08,
    "inventory_stockout_rel_per_pct": -0.012,
    "inventory_holding_cost_rate": 0.02,
    "delay_otif_pp_per_day": -1.8,
    "delay_late_rev_rel_per_day": 0.035,
    "demand_revenue_rel": 1.0,
    "demand_stockout_pp_per_pct": 0.22,
    "demand_otif_pp_per_pct": -0.12,
    "price_elasticity": -0.55,
    "promotion_units": 0.12,
    "promotion_margin_pp": -1.5,
    "note": "SAMPLE elasticities for linear what-if on extract baselines. Not a digital twin of OMS/WMS physics.",
}

# Extract baselines (DataCo + Retail II window 2015-01-01 → 2018-01-31).
BASELINE = {
    "revenue": 31644665.08,
    "profit": 3806420.63,
    "otif_pct": 40.83,
    "stockout_pct": 0.03,
    "coverage": 43.48,
    "late_revenue": 18082555.3,
    "margin_pct": 12.03,
    "on_hand_value": 3879.95e6,
    "sample_otif_target_pct": 92.0,
}

_USAGE: list[dict] = []


def usage() -> dict:
    return {"runs": len(_USAGE), "last": _USAGE[0] if _USAGE else None}


def _round(n: float) -> float:
    return round(n, 2)


def _clamp_otif(n: float) -> float:
    return min(BASELINE["sample_otif_target_pct"], max(0.0, n))


def _pack(shock: dict, projected: dict, extra: list[str] | None = None) -> dict:
    b = {k: BASELINE[k] for k in ("revenue", "profit", "otif_pct", "stockout_pct", "coverage", "late_revenue", "margin_pct")}
    deltas = {k: _round(projected[k] - b[k]) for k in b}
    result = {
        "shock": shock,
        "baseline": b,
        "projected": projected,
        "deltas": deltas,
        "method": "linear SAMPLE elasticities on extract KPIs",
        "limitations": [
            SAMPLE_ELASTICITIES["note"],
            "Does not resimulate orders, fill, or carrier capacity.",
            "OTIF is capped at the SAMPLE 92% enterprise target.",
            *(extra or []),
        ],
    }
    _USAGE.insert(0, {"kind": shock.get("kind")})
    return result


def simulate(shock: dict) -> dict:
    b = {k: BASELINE[k] for k in ("revenue", "profit", "otif_pct", "stockout_pct", "coverage", "late_revenue", "margin_pct")}
    e = SAMPLE_ELASTICITIES
    kind = shock.get("kind")
    if kind == "inventory":
        pct = float(shock["pct"])
        coverage = b["coverage"] * (1 + pct / 100)
        otif_pct = _clamp_otif(b["otif_pct"] + pct * e["inventory_otif_pp_per_pct"])
        stockout_pct = max(0.0, b["stockout_pct"] * (1 + pct * e["inventory_stockout_rel_per_pct"]))
        extra_inv = BASELINE["on_hand_value"] * pct / 100
        profit = b["profit"] - extra_inv * e["inventory_holding_cost_rate"]
        projected = deepcopy(b)
        projected.update(
            coverage=_round(coverage),
            otif_pct=_round(otif_pct),
            stockout_pct=_round(stockout_pct),
            profit=_round(profit),
        )
        return _pack(shock, projected, ["Holding cost proxy 2% of extra on-hand $ (all snapshots, not a balance sheet)."])
    if kind == "supplier_delay":
        d = float(shock["days"])
        projected = deepcopy(b)
        projected["otif_pct"] = _round(_clamp_otif(b["otif_pct"] + d * e["delay_otif_pp_per_day"]))
        projected["late_revenue"] = _round(b["late_revenue"] * (1 + d * e["delay_late_rev_rel_per_day"]))
        projected["profit"] = _round(b["profit"] * (1 - 0.004 * d))
        return _pack(shock, projected, ["Lead-time shock is uniform; Fan Shop concentration is not re-weighted."])
    if kind == "demand":
        pct = float(shock["pct"])
        projected = deepcopy(b)
        projected["revenue"] = _round(b["revenue"] * (1 + (pct / 100) * e["demand_revenue_rel"]))
        projected["stockout_pct"] = _round(max(0.0, b["stockout_pct"] + pct * e["demand_stockout_pp_per_pct"]))
        projected["otif_pct"] = _round(_clamp_otif(b["otif_pct"] + pct * e["demand_otif_pp_per_pct"]))
        projected["profit"] = _round(b["profit"] * (1 + (pct / 100) * 0.7))
        return _pack(shock, projected)
    if kind == "price":
        pct = float(shock["pct"])
        qty = 1 + (pct / 100) * e["price_elasticity"]
        projected = deepcopy(b)
        projected["revenue"] = _round(b["revenue"] * (1 + pct / 100) * qty)
        projected["profit"] = _round(b["profit"] * (1 + pct / 100) * qty)
        return _pack(shock, projected, [f"Price elasticity SAMPLE {e['price_elasticity']}."])
    # promotion
    revenue = b["revenue"] * (1 + e["promotion_units"])
    margin_pct = b["margin_pct"] + e["promotion_margin_pp"]
    projected = deepcopy(b)
    projected.update(
        revenue=_round(revenue),
        margin_pct=_round(margin_pct),
        profit=_round(revenue * (margin_pct / 100)),
        stockout_pct=_round(b["stockout_pct"] + 2.4),
        otif_pct=_round(_clamp_otif(b["otif_pct"] - 1.4)),
    )
    return _pack(shock, projected)


def describe_shock(shock: dict) -> str:
    kind = shock.get("kind")
    if kind == "inventory":
        pct = shock["pct"]
        return f"Inventory {'increase' if pct >= 0 else 'decrease'} of {abs(pct)}%"
    if kind == "supplier_delay":
        return f"Supplier lead time +{shock['days']} days"
    if kind == "demand":
        return f"Demand surge {shock['pct']}%"
    if kind == "price":
        pct = shock["pct"]
        return f"Price {'increase' if pct >= 0 else 'decrease'} of {abs(pct)}%"
    return "Promotion launch (SAMPLE +12% units, −1.5pp margin)"
