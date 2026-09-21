"""Offline A/B testing utilities (no live experiment platform)."""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats

try:
    from inference_stats import mean_ci, proportion_ci, welch_test
except ImportError:
    from .inference_stats import mean_ci, proportion_ci, welch_test


def two_proportion_ztest(success_a: int, n_a: int, success_b: int, n_b: int) -> dict[str, Any]:
    p1, p2 = success_a / n_a, success_b / n_b
    p = (success_a + success_b) / (n_a + n_b)
    se = np.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    z = (p1 - p2) / se if se else 0.0
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    return {
        "test": "two-proportion z-test (unpooled SE under H0)",
        "p_a": p1,
        "p_b": p2,
        "lift_b_minus_a": p2 - p1,
        "z": float(z),
        "p_value": float(pval),
        "ci_a": proportion_ci(success_a, n_a),
        "ci_b": proportion_ci(success_b, n_b),
        "methodology": "Fixed-horizon frequentist test. No sequential peeking correction.",
        "assumptions": ["Independent Bernoulli trials", "Users/orders randomized (not true in this extract)"],
        "limitations": [
            "This warehouse is observational; treat results as a calculator demo unless you supply randomized counts",
        ],
    }


def cuped_note() -> str:
    return (
        "CUPED / sequential testing / CUPAC are not implemented. "
        "Use this module only as a transparent calculator on counts you trust."
    )


def continuous_ab(a, b) -> dict[str, Any]:
    return {
        "arm_a": mean_ci(a),
        "arm_b": mean_ci(b),
        "comparison": welch_test(a, b),
        "note": cuped_note(),
    }
