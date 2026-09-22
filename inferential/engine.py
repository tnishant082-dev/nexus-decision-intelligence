"""Estimators for binary contrasts.

The output is an association with a stated adjustment. It does not become a
causal effect because the interval excludes zero.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def _as_arrays(y, treat, stratum):
    y = np.asarray(y, dtype=float)
    treat = np.asarray(treat, dtype=int)
    stratum = np.asarray(stratum)
    ok = np.isfinite(y) & np.isin(treat, (0, 1))
    return y[ok], treat[ok], stratum[ok]


def _arm_rate(y: np.ndarray) -> tuple[float, int]:
    n = int(y.size)
    if n == 0:
        return float("nan"), 0
    return float(y.mean()), n


def _binomial_var(p: float, n: int) -> float:
    if n <= 0 or not np.isfinite(p):
        return float("inf")
    return max(p * (1.0 - p), 1e-8) / n


def stratified_risk_difference(
    y,
    treat,
    stratum,
    min_cell: int = 20,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Inverse-variance stratified risk difference, plus the unadjusted contrast.

    ``treat`` is 1 for the focal arm and 0 for the reference arm.
    Strata smaller than ``min_cell`` on either arm are dropped, not pooled back in.
    """
    outcome, arm, strata = _as_arrays(y, treat, stratum)
    n = int(outcome.size)
    n1 = int((arm == 1).sum())
    n0 = int((arm == 0).sum())
    if n1 == 0 or n0 == 0:
        return {
            "ok": False,
            "error": "both arms need observations",
            "n": n,
            "n_treated": n1,
            "n_control": n0,
        }

    p1, _ = _arm_rate(outcome[arm == 1])
    p0, _ = _arm_rate(outcome[arm == 0])
    naive = p1 - p0
    naive_se = float(np.sqrt(_binomial_var(p1, n1) + _binomial_var(p0, n0)))

    weights: list[float] = []
    diffs: list[float] = []
    used = 0
    dropped = 0
    for level in pd_unique(strata):
        in_level = strata == level
        y1 = outcome[in_level & (arm == 1)]
        y0 = outcome[in_level & (arm == 0)]
        n1k, n0k = int(y1.size), int(y0.size)
        if n1k < min_cell or n0k < min_cell:
            dropped += 1
            continue
        p1k, _ = _arm_rate(y1)
        p0k, _ = _arm_rate(y0)
        var_k = _binomial_var(p1k, n1k) + _binomial_var(p0k, n0k)
        if not np.isfinite(var_k) or var_k <= 0:
            dropped += 1
            continue
        weights.append(1.0 / var_k)
        diffs.append(p1k - p0k)
        used += 1

    if used == 0:
        return {
            "ok": False,
            "error": f"no stratum had at least {min_cell} units on both arms",
            "n": n,
            "n_treated": n1,
            "n_control": n0,
            "strata_dropped": dropped,
            "naive_risk_difference": naive,
            "naive_se": naive_se,
            "p_treated": p1,
            "p_control": p0,
        }

    w = np.asarray(weights, dtype=float)
    rd = np.asarray(diffs, dtype=float)
    weight_sum = float(w.sum())
    adjusted = float((w * rd).sum() / weight_sum)
    se = float(np.sqrt(1.0 / weight_sum))
    z = float(stats.norm.ppf(1 - alpha / 2))
    return {
        "ok": True,
        "method": "inverse-variance weighted stratified risk difference",
        "alpha": alpha,
        "n": n,
        "n_treated": n1,
        "n_control": n0,
        "p_treated": p1,
        "p_control": p0,
        "naive_risk_difference": float(naive),
        "naive_se": naive_se,
        "adjusted_risk_difference": adjusted,
        "se": se,
        "ci_low": adjusted - z * se,
        "ci_high": adjusted + z * se,
        "z": z,
        "strata_used": used,
        "strata_dropped": dropped,
        "min_cell": min_cell,
    }


def pd_unique(values: np.ndarray) -> list:
    """Order-stable unique labels without requiring pandas."""
    seen: list = []
    for value in values.tolist():
        if value not in seen:
            seen.append(value)
    return seen


def nullification_bias(estimate: float, se: float, z: float = 1.96) -> float:
    """Smallest absolute bias that pulls a normal 95% interval onto zero.

    This is a bound in outcome units, not a proof that no such bias exists.
    """
    if not np.isfinite(estimate) or not np.isfinite(se) or se < 0:
        return float("nan")
    return float(max(0.0, abs(estimate) - z * se))


def evalue_risk_ratio(p_treated: float, p_control: float) -> dict[str, Any]:
    """VanderWeele E-value for the point risk ratio. Undefined if a rate is 0."""
    if p_control <= 0 or p_treated <= 0 or not np.isfinite(p_treated) or not np.isfinite(p_control):
        return {
            "evalue": None,
            "risk_ratio": None,
            "note": "E-value omitted because a arm rate is zero or undefined.",
        }
    rr = p_treated / p_control
    reported = rr
    if rr < 1:
        rr = 1.0 / rr
    evalue = 1.0 if rr <= 1 else float(rr + np.sqrt(rr * (rr - 1.0)))
    return {
        "evalue": evalue,
        "risk_ratio": float(reported),
        "note": (
            "Approximate confounding strength, on the risk-ratio scale, that could "
            "explain away the point estimate. It does not validate the design."
        ),
    }


def leave_one_stratum_out(y, treat, stratum, min_cell: int = 20) -> dict[str, Any]:
    """Refit once with each included stratum removed.

    A sign flip means one category is carrying the contrast. The ranking is
    then too brittle to act on.
    """
    full = stratified_risk_difference(y, treat, stratum, min_cell=min_cell)
    if not full.get("ok") or int(full.get("strata_used") or 0) < 2:
        return {
            "checked": False,
            "sign_flip": False,
            "strata_checked": 0,
            "reason": "Leave-one-out needs two strata that pass the cell minimum.",
        }
    outcome, arm, strata = _as_arrays(y, treat, stratum)
    base = float(full["adjusted_risk_difference"])
    worst = None
    max_shift = 0.0
    flip = False
    checked = 0
    for level in pd_unique(strata):
        keep = strata != level
        refit = stratified_risk_difference(outcome[keep], arm[keep], strata[keep], min_cell=min_cell)
        if not refit.get("ok"):
            continue
        if int(refit["strata_used"]) >= int(full["strata_used"]):
            continue
        checked += 1
        estimate = float(refit["adjusted_risk_difference"])
        shift = abs(estimate - base)
        if shift >= max_shift:
            max_shift = shift
            worst = str(level)
        if base * estimate < 0 and abs(base) >= 0.01:
            flip = True
    return {
        "checked": checked > 0,
        "sign_flip": flip,
        "strata_checked": checked,
        "max_shift": max_shift,
        "worst_stratum": worst,
        "method": "Refit the stratified risk difference once per included stratum.",
    }


def association_signal(ci_low: float, ci_high: float, minimum_practical_effect: float) -> str:
    """What the interval says before identification is allowed to override it.

    ``minimum_practical_effect`` is a positive risk difference. The focal arm
    is worse when its outcome rate is higher.
    """
    mpe = abs(minimum_practical_effect)
    if ci_low > mpe:
        return "prioritize"
    if ci_high < -mpe:
        return "do_not_prioritize"
    return "hold"
