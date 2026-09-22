"""Registered studies on the local warehouse.

Two claims are pre-specified:

* ``warehouse_late_gap`` — mix-adjusted late-rate gap for the warehouse with the
  largest late-line revenue pool. Used to rank investigation, not to estimate
  the effect of moving orders.
* ``advance_selection`` — late rate on advance shipments versus the rest.
  The contrast is computed and then refused as a causal claim, because
  ``is_advance`` is chosen when delay risk is already high.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from inferential.engine import (
    association_signal,
    evalue_risk_ratio,
    leave_one_stratum_out,
    nullification_bias,
    stratified_risk_difference,
)
from inferential.power import design_power

DB = Path(__file__).resolve().parents[1] / "data-engineering" / "warehouse" / "nexus.duckdb"

STUDY_IDS = ("warehouse_late_gap", "advance_selection")
MINIMUM_PRACTICAL_EFFECT = 0.02
MIN_CELL = 20
MIN_ARM = 30


def run_board(db: Path | None = None) -> dict[str, Any]:
    studies = [run_study(study_id, db=db) for study_id in STUDY_IDS]
    return {
        "discipline": "inferential_engineering",
        "not": "llm_inference_gateway",
        "minimum_practical_effect": MINIMUM_PRACTICAL_EFFECT,
        "studies": studies,
    }


def claim_summary(db: Path | None = None) -> dict[str, Any]:
    """One line for the investigate path. Never raises."""
    try:
        card = run_study("warehouse_late_gap", db=db)
    except Exception as exc:  # noqa: BLE001 — investigate must survive a missing warehouse
        return {
            "ok": False,
            "causal_claim": False,
            "line": f"Inferential board unavailable: {exc}",
        }
    if not card.get("ok"):
        return {
            "ok": False,
            "causal_claim": False,
            "study_id": "warehouse_late_gap",
            "line": card.get("error") or "Inferential board unavailable.",
        }
    estimate = card["estimate"]
    decision = card["decision"]
    warehouse = card["estimand"]["target_warehouse"]
    return {
        "ok": True,
        "causal_claim": False,
        "study_id": "warehouse_late_gap",
        "verdict": decision["verdict"],
        "target_warehouse": warehouse,
        "adjusted_risk_difference_pp": estimate["adjusted_risk_difference_pp"],
        "ci_low_pp": estimate["ci_low_pp"],
        "ci_high_pp": estimate["ci_high_pp"],
        "line": (
            f"Inferential engineering: {warehouse} mix-adjusted late-rate gap "
            f"{estimate['adjusted_risk_difference_pp']} pp "
            f"(95% CI {estimate['ci_low_pp']} to {estimate['ci_high_pp']}). "
            f"Verdict {decision['verdict']}. Not a causal effect of moving orders."
        ),
    }


def run_study(study_id: str, db: Path | None = None) -> dict[str, Any]:
    if study_id not in STUDY_IDS:
        return {"ok": False, "study_id": study_id, "error": "unknown study"}
    path = Path(db) if db is not None else DB
    if not path.exists():
        return {
            "ok": False,
            "study_id": study_id,
            "error": f"warehouse missing at {path}. Run python data-engineering/run_pipeline.py",
        }
    try:
        con = duckdb.connect(str(path), read_only=True)
        try:
            if study_id == "warehouse_late_gap":
                return _warehouse_late_gap(con)
            return _advance_selection(con)
        finally:
            con.close()
    except Exception as exc:  # noqa: BLE001 — surface schema/SQL failures as a card, not a 500
        return {"ok": False, "study_id": study_id, "error": str(exc)}


def _warehouse_late_gap(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    target = con.execute(
        """
        SELECT w.warehouse_name
        FROM fact_orders o
        JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
        GROUP BY 1
        ORDER BY SUM(CASE WHEN o.is_revenue = 1 AND o.is_late = 1 THEN o.net_sales ELSE 0 END) DESC
        LIMIT 1
        """
    ).fetchone()
    if not target or not target[0]:
        return {"ok": False, "study_id": "warehouse_late_gap", "error": "no warehouse late-revenue pool"}
    warehouse = str(target[0])
    frame = con.execute(
        """
        SELECT
          order_id,
          arg_max(warehouse_name, sales) AS warehouse_name,
          COALESCE(arg_max(category_name, sales), 'UNKNOWN') AS category_name,
          MAX(is_late)::INTEGER AS is_late
        FROM (
          SELECT
            o.order_id,
            w.warehouse_name,
            p.category_name,
            CASE WHEN o.is_revenue = 1 THEN o.net_sales ELSE 0 END AS sales,
            o.is_late
          FROM fact_orders o
          JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
          JOIN dim_product p ON o.product_key = p.product_key
        )
        GROUP BY order_id
        """
    ).fetchdf()
    treat = (frame["warehouse_name"] == warehouse).astype(int)
    fit = stratified_risk_difference(
        frame["is_late"],
        treat,
        frame["category_name"],
        min_cell=MIN_CELL,
    )
    stability = leave_one_stratum_out(frame["is_late"], treat, frame["category_name"], min_cell=MIN_CELL)
    card = _card(
        study_id="warehouse_late_gap",
        title=f"Mix-adjusted late rate at {warehouse} versus the rest of the network",
        estimand={
            "unit": "order",
            "outcome": "1 if any line on the order is late",
            "contrast": f"{warehouse} versus every other warehouse",
            "population": "orders in the local public extract",
            "target_warehouse": warehouse,
            "adjustment": "dominant product category on the order, by line sales",
            "target_rule": "warehouse with the largest late-line revenue pool",
        },
        identification={
            "class": "mix_adjusted_association",
            "causal_claim": False,
            "assumptions": [
                "Order grain is the decision unit; a late flag on any line marks the order late",
                "Dominant category removes part of the product-mix difference across warehouses",
                "Orders are independent after that stratification",
            ],
            "failures": [
                "Warehouse assignment is not randomized",
                "Carrier, season, and customer mix are not in the adjustment set",
                "A gap is a reason to investigate, not an effect of relocating orders",
            ],
        },
        fit=fit,
        override_verdict=None,
        stability=stability,
        action_for={
            "prioritize": (
                f"Investigate {warehouse} before spending expedite budget. "
                "The mix-adjusted late-rate gap clears the practical threshold."
            ),
            "hold": (
                "Do not fund a warehouse program from this contrast. "
                "The interval still includes gaps smaller than the practical threshold."
            ),
            "do_not_prioritize": (
                f"{warehouse} is not later than the rest of the network after category adjustment."
            ),
            "underpowered": (
                f"Do not open a program at {warehouse}. "
                "At 80% power this extract cannot see a 2 percentage-point late-rate gap."
            ),
            "unstable": (
                f"Do not rank {warehouse} yet. Removing one product category flips the sign of the gap."
            ),
        },
    )
    return card


def _advance_selection(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    frame = con.execute(
        """
        SELECT
          s.is_late::INTEGER AS is_late,
          s.is_advance::INTEGER AS is_advance,
          COALESCE(w.warehouse_name, 'UNKNOWN') AS warehouse_name
        FROM fact_shipments s
        LEFT JOIN dim_warehouse w ON s.warehouse_key = w.warehouse_key
        WHERE s.is_late IS NOT NULL AND s.is_advance IS NOT NULL
        """
    ).fetchdf()
    fit = stratified_risk_difference(
        frame["is_late"],
        frame["is_advance"],
        frame["warehouse_name"],
        min_cell=MIN_CELL,
    )
    stability = leave_one_stratum_out(
        frame["is_late"], frame["is_advance"], frame["warehouse_name"], min_cell=MIN_CELL
    )
    return _card(
        study_id="advance_selection",
        title="Late rate on advance shipments versus other shipments",
        estimand={
            "unit": "shipment",
            "outcome": "shipment is late",
            "contrast": "is_advance = 1 versus is_advance = 0",
            "population": "shipments in the local public extract",
            "adjustment": "warehouse",
            "target_warehouse": None,
        },
        identification={
            "class": "selected_treatment",
            "causal_claim": False,
            "assumptions": [
                "The shipment flag is coded consistently",
                "Warehouse stratification only removes warehouse mix",
            ],
            "failures": [
                "is_advance is selected when delay risk is already high",
                "The outcome and the decision to advance share causes that are not observed",
                "A significant contrast is not the effect of cutting or expanding advance freight",
            ],
        },
        fit=fit,
        override_verdict="do_not_claim",
        stability=stability,
        action_for={
            "do_not_claim": (
                "Do not change advance-shipping policy from this contrast. "
                "The flag is chosen after delay risk is already visible."
            ),
        },
    )


def _card(
    study_id: str,
    title: str,
    estimand: dict,
    identification: dict,
    fit: dict,
    override_verdict: str | None,
    action_for: dict[str, str],
    stability: dict | None = None,
) -> dict[str, Any]:
    if not fit.get("ok"):
        return {
            "ok": False,
            "study_id": study_id,
            "title": title,
            "estimand": estimand,
            "identification": identification,
            "error": fit.get("error"),
            "estimate": _public_estimate(fit) if fit.get("naive_risk_difference") is not None else None,
        }

    signal = association_signal(
        fit["ci_low"],
        fit["ci_high"],
        MINIMUM_PRACTICAL_EFFECT,
    )
    if fit["n_treated"] < MIN_ARM or fit["n_control"] < MIN_ARM:
        signal = "hold"
        sample_note = f"An arm has fewer than {MIN_ARM} units, so the signal is held."
    else:
        sample_note = None

    power = design_power(
        fit["n_treated"],
        fit["n_control"],
        fit["p_control"],
        MINIMUM_PRACTICAL_EFFECT,
    )
    stability = stability or {"checked": False, "sign_flip": False}
    if override_verdict:
        verdict = override_verdict
    elif sample_note:
        verdict = "hold"
    elif signal == "prioritize" and stability.get("sign_flip"):
        verdict = "unstable"
    elif signal == "hold" and not power["powered_for_practical_effect"]:
        verdict = "underpowered"
    else:
        verdict = signal
    reason = _reason(verdict, override_verdict, signal, sample_note, power, stability)
    shift = fit["naive_risk_difference"] - fit["adjusted_risk_difference"]
    crude_evalue = evalue_risk_ratio(fit["p_treated"], fit["p_control"])
    crude_evalue["applies_to"] = "crude arm rates, not the stratified risk difference"
    sensitivity = {
        "nullification_bias": nullification_bias(fit["adjusted_risk_difference"], fit["se"], fit["z"]),
        "nullification_bias_pp": _pp(nullification_bias(fit["adjusted_risk_difference"], fit["se"], fit["z"])),
        "adjustment_shift": shift,
        "adjustment_shift_pp": _pp(shift),
        "evalue": crude_evalue,
        "reading": (
            "Nullification bias is the smallest constant shift, in risk-difference units, "
            "that would pull this 95% interval onto zero. It is not evidence that the shift is absent."
        ),
    }
    return {
        "ok": True,
        "study_id": study_id,
        "title": title,
        "pipeline": [
            "estimand",
            "identification",
            "estimator",
            "uncertainty",
            "sensitivity",
            "power",
            "stability",
            "decision",
        ],
        "estimand": estimand,
        "identification": identification,
        "estimate": _public_estimate(fit),
        "statistical_signal": signal,
        "sensitivity": sensitivity,
        "power": power,
        "stability": stability,
        "decision": {
            "verdict": verdict,
            "overrides_signal": override_verdict is not None,
            "minimum_practical_effect": MINIMUM_PRACTICAL_EFFECT,
            "minimum_practical_effect_pp": _pp(MINIMUM_PRACTICAL_EFFECT),
            "rule": (
                "Prioritize only when the entire 95% interval sits above the practical threshold, "
                "leave-one-stratum-out does not flip the sign, and identification allows a ranking. "
                "A hold on an underpowered contrast is reported as underpowered. "
                "A selected treatment is do_not_claim even when the interval is large."
            ),
            "reason": reason,
            "action": action_for.get(verdict, "Hold the action."),
            "causal_claim": False,
        },
        "limitations": identification["failures"],
    }


def _public_estimate(fit: dict) -> dict[str, Any]:
    out: dict[str, Any] = {
        "method": fit.get("method"),
        "n": fit.get("n"),
        "n_treated": fit.get("n_treated"),
        "n_control": fit.get("n_control"),
        "strata_used": fit.get("strata_used"),
        "strata_dropped": fit.get("strata_dropped"),
        "min_cell": fit.get("min_cell"),
    }
    for key in (
        "p_treated",
        "p_control",
        "naive_risk_difference",
        "adjusted_risk_difference",
        "se",
        "ci_low",
        "ci_high",
    ):
        if key in fit and fit[key] is not None:
            out[key] = fit[key]
            out[f"{key}_pp"] = _pp(fit[key]) if key != "se" else _pp(fit[key])
    if "se" in out:
        out["se_pp"] = _pp(fit["se"])
    return out


def _pp(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        if value != value:  # NaN
            return None
    except TypeError:
        return None
    return round(100.0 * float(value), 2)


def _reason(
    verdict: str,
    override: str | None,
    signal: str,
    sample_note: str | None,
    power: dict | None = None,
    stability: dict | None = None,
) -> str:
    if override == "do_not_claim":
        base = (
            f"The interval's own signal is '{signal}', and the decision is still do_not_claim. "
            "Identification fails: the focal flag is selected, so significance is not an effect."
        )
    elif verdict == "prioritize":
        base = "The mix-adjusted 95% interval lies entirely above the practical threshold, and no single stratum flips the sign."
    elif verdict == "unstable":
        worst = (stability or {}).get("worst_stratum")
        base = (
            "The interval clears the practical threshold, but removing one stratum flips the sign. "
            f"The contrast is too brittle to rank. Worst stratum: {worst}."
        )
    elif verdict == "underpowered":
        mde = (power or {}).get("minimum_detectable_effect_pp")
        base = (
            f"The interval does not clear 2 percentage points, and the 80% minimum detectable effect "
            f"is {mde} pp. The extract cannot support that ranking."
        )
    elif verdict == "do_not_prioritize":
        base = "The mix-adjusted 95% interval lies entirely below the negative practical threshold."
    else:
        base = "The interval does not clear the practical threshold, so the action stays on hold."
    if sample_note:
        return f"{base} {sample_note}"
    return base


if __name__ == "__main__":
    import json

    print(json.dumps(run_board(), indent=2, default=str)[:4000])
