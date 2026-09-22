"""One next action from the registered studies.

Investigate a warehouse only when the mix-adjusted gap clears the practical
threshold and leave-one-stratum-out keeps the same sign. Advance shipping is
never that action: the study is refused as a selected treatment.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.agents.cards import EXTRACT_WINDOW, stamp
from inferential.studies import run_study


def next_action(db: Path | None = None) -> dict[str, Any]:
    gap = run_study("warehouse_late_gap", db=db)
    advance = run_study("advance_selection", db=db)
    refused = _refused(advance)
    if not gap.get("ok"):
        return {
            "ok": False,
            "decision": "hold",
            "error": gap.get("error") or "warehouse study did not run",
            "refused": refused,
            "extract_window": EXTRACT_WINDOW,
            "causal_claim": False,
        }

    verdict = gap["decision"]["verdict"]
    if verdict == "prioritize":
        decision = "investigate"
        metric_id = "late_revenue"
    else:
        decision = "hold"
        metric_id = "inferential"
    bound = stamp(gap["decision"]["action"], metric_id)
    exposure = _exposure(db, gap["estimand"].get("target_warehouse"))
    return {
        "ok": True,
        "decision": decision,
        "verdict": verdict,
        "action": gap["decision"]["action"],
        "because": gap["decision"]["reason"],
        "warehouse": gap["estimand"].get("target_warehouse"),
        "adjusted_risk_difference_pp": gap["estimate"].get("adjusted_risk_difference_pp"),
        "ci_low_pp": gap["estimate"].get("ci_low_pp"),
        "ci_high_pp": gap["estimate"].get("ci_high_pp"),
        "power": gap.get("power"),
        "stability": gap.get("stability"),
        "nullification_bias_pp": (gap.get("sensitivity") or {}).get("nullification_bias_pp"),
        "late_revenue_exposure": exposure,
        "metric": bound["metric"],
        "means": bound["means"],
        "does_not_mean": bound["does_not_mean"],
        "extract_window": EXTRACT_WINDOW,
        "causal_claim": False,
        "refused": refused,
    }


def _refused(advance: dict) -> list[dict[str, Any]]:
    if not advance.get("ok"):
        return [{
            "study_id": "advance_selection",
            "verdict": "do_not_claim",
            "action": advance.get("error") or "Advance-shipping study did not run, so it cannot be an action.",
        }]
    return [{
        "study_id": "advance_selection",
        "verdict": advance["decision"]["verdict"],
        "action": advance["decision"]["action"],
    }]


def _exposure(db: Path | None, warehouse: str | None) -> dict[str, Any] | None:
    """Late-line dollars for the ranked warehouse, when the full warehouse is present."""
    try:
        from decisions.economics import warehouse_exceptions

        rows = warehouse_exceptions(db) if db is not None else warehouse_exceptions()
    except Exception:
        return None
    for row in rows:
        if warehouse is None or row.get("warehouse_name") == warehouse:
            return {
                "warehouse_name": row.get("warehouse_name"),
                "late_revenue": row.get("late_revenue"),
                "means": "Sales dollars on late lines at this warehouse. Service-risk exposure.",
                "does_not_mean": "Lost sales or recovered EBITDA.",
            }
    return None
