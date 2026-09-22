"""Design power for a two-arm risk difference.

The minimum detectable effect uses the control-arm rate for both arms.
That approximation is standard for planning and is conservative when the
true gap is large. It does not turn an observational contrast into an experiment.
"""
from __future__ import annotations

import math

from scipy import stats


def minimum_detectable_effect(
    n_treated: int,
    n_control: int,
    baseline_rate: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> float:
    """Smallest absolute risk difference detectable at the given power."""
    if n_treated <= 0 or n_control <= 0:
        return float("inf")
    rate = min(max(float(baseline_rate), 0.01), 0.99)
    z_alpha = float(stats.norm.ppf(1 - alpha / 2))
    z_power = float(stats.norm.ppf(power))
    se = math.sqrt(rate * (1.0 - rate) * (1.0 / n_treated + 1.0 / n_control))
    return (z_alpha + z_power) * se


def design_power(
    n_treated: int,
    n_control: int,
    baseline_rate: float,
    practical_effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> dict:
    mde = minimum_detectable_effect(n_treated, n_control, baseline_rate, alpha, power)
    return {
        "alpha": alpha,
        "power": power,
        "baseline_rate": None if baseline_rate != baseline_rate else float(baseline_rate),
        "n_treated": int(n_treated),
        "n_control": int(n_control),
        "minimum_detectable_effect": mde,
        "minimum_detectable_effect_pp": None if not math.isfinite(mde) else round(100.0 * mde, 2),
        "practical_effect": practical_effect,
        "practical_effect_pp": round(100.0 * practical_effect, 2),
        "powered_for_practical_effect": bool(math.isfinite(mde) and mde <= abs(practical_effect)),
        "method": (
            "Two-sided normal approximation for a risk difference. "
            "Variance is computed at the control rate for both arms."
        ),
    }
