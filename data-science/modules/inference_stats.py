"""Statistical helpers: CIs, tests, documented insights."""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def mean_ci(x, alpha: float = 0.05) -> dict[str, float]:
    arr = np.asarray(x, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = len(arr)
    if n < 2:
        return {"n": n, "mean": float(arr.mean()) if n else None, "ci_low": None, "ci_high": None, "alpha": alpha}
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / np.sqrt(n))
    tcrit = float(stats.t.ppf(1 - alpha / 2, n - 1))
    return {
        "n": n,
        "mean": mean,
        "std": float(arr.std(ddof=1)),
        "ci_low": mean - tcrit * se,
        "ci_high": mean + tcrit * se,
        "alpha": alpha,
        "method": "Student t interval on the mean (iid assumption)",
    }


def welch_test(a, b) -> dict[str, Any]:
    t, p = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    return {
        "test": "Welch two-sample t-test",
        "statistic": float(t),
        "p_value": float(p),
        "significant_at_0.05": bool(p < 0.05),
        "assumptions": [
            "Independent observations (order lines in a public extract may be clustered)",
            "Approximate normality of means via CLT; variances need not be equal",
        ],
        "limitations": [
            "Not a randomized experiment; p-values are descriptive",
            "Large n makes tiny differences 'significant'",
        ],
    }


def proportion_ci(successes: int, n: int, alpha: float = 0.05) -> dict[str, float]:
    if n <= 0:
        return {"n": 0, "p": None}
    p = successes / n
    z = float(stats.norm.ppf(1 - alpha / 2))
    se = np.sqrt(p * (1 - p) / n)
    return {
        "n": n,
        "p": p,
        "ci_low": max(0.0, p - z * se),
        "ci_high": min(1.0, p + z * se),
        "method": "Wald interval (normal approximation)",
        "limitations": ["Poor coverage near 0/1; Wilson interval preferred for small n"],
    }
