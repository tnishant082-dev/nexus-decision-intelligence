"""Wilson score interval — no scipy required so economics can import it cold."""
from __future__ import annotations

import math


def wilson_interval(successes: int, n: int, z: float = 1.96) -> dict:
    if n <= 0:
        return {"center": None, "lo": None, "hi": None, "n": 0, "successes": 0}
    p = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n) / denom
    return {
        "center": round(100 * center, 2),
        "lo": round(100 * max(0.0, center - margin), 2),
        "hi": round(100 * min(1.0, center + margin), 2),
        "n": int(n),
        "successes": int(successes),
        "method": "Wilson score interval (percent)",
    }
