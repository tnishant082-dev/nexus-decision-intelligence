"""Action cards that cannot drop their metric meaning.

Every card carries the extract window and what the number is allowed to mean.
A recommendation that quotes dollars still cannot be read as lost sales.
"""
from __future__ import annotations

EXTRACT_WINDOW = "2015-01-01 → 2018-01-31"

# metric id -> (short name, what it is, what it must not be turned into)
_DEFINITIONS: dict[str, tuple[str, str, str]] = {
    "late_revenue": (
        "late-line revenue",
        "Sales dollars on lines that shipped late. Service-risk exposure.",
        "Lost sales, recovered revenue, or EBITDA.",
    ),
    "delay_cost": (
        "delay cost",
        "The extract field delay_cost on shipments.",
        "A measured P&L loss, or proof the dollars were forfeited.",
    ),
    "expedite_freight": (
        "expedite freight",
        "Freight on shipments flagged is_advance.",
        "Proof that cutting advance freight recovers revenue.",
    ),
    "inventory": (
        "inventory coverage",
        "A snapshot-weighted coverage and turns proxy.",
        "A balance-sheet cash balance or statutory inventory.",
    ),
    "stockout": (
        "stockout rate",
        "Share of inventory snapshot rows flagged as stockout.",
        "Lost sales caused by those stockouts.",
    ),
    "churn_proxy": (
        "180-day inactivity",
        "Customers with no order in the last 180 days of this extract.",
        "Contracted churn, or revenue already lost.",
    ),
    "growth": (
        "calendar revenue",
        "Revenue lines summed by calendar year inside the extract.",
        "A structural decline. 2018 is a partial month, not a full year.",
    ),
    "otif": (
        "OTIF",
        "Share of orders whose lines were all on time and in full.",
        "A revenue figure. Low OTIF is a service gap, not lost sales.",
    ),
    "vendor_sla": (
        "vendor on-time receipt",
        "A check against preferred-vendor mix and SAMPLE receipt guidance.",
        "A measured penalty or a revenue claim.",
    ),
    "sample_policy": (
        "SAMPLE policy",
        "Guidance from a document labeled SAMPLE in this repo.",
        "A live company SOP or a financial commitment.",
    ),
    "inferential": (
        "mix-adjusted late-rate gap",
        "An adjusted association used to rank which warehouse to investigate.",
        "A causal effect of moving orders, lost sales, or recovered EBITDA.",
    ),
}


def stamp(action: str, metric_id: str) -> dict:
    """Bind one recommendation to its definition and the extract window."""
    if metric_id not in _DEFINITIONS:
        raise KeyError(f"unknown metric semantics: {metric_id}")
    name, means, does_not_mean = _DEFINITIONS[metric_id]
    return {
        "action": action,
        "metric_id": metric_id,
        "metric": name,
        "means": means,
        "does_not_mean": does_not_mean,
        "extract_window": EXTRACT_WINDOW,
        "held": False,
    }


def note_metric(text: str) -> str:
    """Pick the definition for an evidence note the decision agent forwards."""
    lowered = text.lower()
    if "churn" in lowered or "inactivity" in lowered or "ltv" in lowered:
        return "churn_proxy"
    if "stockout" in lowered:
        return "stockout"
    if "forecast" in lowered or "2016" in lowered or "2017" in lowered:
        return "growth"
    return "inventory"
