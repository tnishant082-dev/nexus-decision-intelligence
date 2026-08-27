"""Model router with honest local mock timings (no fake GPUs)."""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass

@dataclass
class RouteDecision:
    label: str  # mock | small | large
    reason: str
    simulated_latency_ms: float

def route(prompt: str, force: str | None = None) -> RouteDecision:
    if force in {"mock", "small", "large"}:
        latency = {"mock": 12.0, "small": 85.0, "large": 420.0}[force]
        return RouteDecision(force, f"forced:{force}", latency)
    n = len(prompt or "")
    # simple heuristic
    if n < 120:
        return RouteDecision("mock", "short_prompt_local_template", 15.0)
    if n < 800:
        return RouteDecision("small", "medium_prompt_small_model_slot", 95.0)
    return RouteDecision("large", "long_prompt_large_model_slot", 450.0)

def generate(prompt: str, force: str | None = None) -> dict:
    decision = route(prompt, force=force)
    t0 = time.perf_counter()
    # simulate work proportional to label (sleep capped for tests)
    time.sleep(min(decision.simulated_latency_ms / 1000.0, 0.05))
    elapsed = (time.perf_counter() - t0) * 1000
    # mock completion text
    digest = hashlib.sha1(prompt.encode()).hexdigest()[:8]
    text = (
        f"[NEXUS {decision.label} router] "
        f"Acknowledged prompt ({len(prompt)} chars). "
        f"This is a local mock completion (id={digest}). "
        f"Route reason: {decision.reason}."
    )
    # rough token estimate
    tokens_in = max(1, len(prompt.split()))
    tokens_out = max(1, len(text.split()))
    return {
        "text": text,
        "route": decision.label,
        "reason": decision.reason,
        "latency_ms": round(elapsed, 2),
        "simulated_target_ms": decision.simulated_latency_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "hardware": "cpu_local_mock",
        "note": "No GPU claimed. Latencies are local mock timings for router benchmarks.",
    }
