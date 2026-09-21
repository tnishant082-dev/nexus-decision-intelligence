"""Model router with honest local mock timings; optional live HTTP providers."""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass

from inference.providers import complete_http, configured_targets


@dataclass
class RouteDecision:
    label: str  # mock | small | large | openai | groq | ollama | vllm | llamacpp
    reason: str
    simulated_latency_ms: float


def route(prompt: str, force: str | None = None) -> RouteDecision:
    provider = (force or os.getenv("NEXUS_LLM_PROVIDER") or "mock").lower()
    targets = {t["label"]: t for t in configured_targets()}
    if provider in targets:
        return RouteDecision(provider, f"env_or_force:{provider}", 0.0)
    if force in {"mock", "small", "large"}:
        latency = {"mock": 12.0, "small": 85.0, "large": 420.0}[force]
        return RouteDecision(force, f"forced:{force}", latency)
    n = len(prompt or "")
    if n < 120:
        return RouteDecision("mock", "short_prompt_local_template", 15.0)
    if n < 800:
        return RouteDecision("small", "medium_prompt_small_model_slot", 95.0)
    return RouteDecision("large", "long_prompt_large_model_slot", 450.0)


def generate(prompt: str, force: str | None = None) -> dict:
    decision = route(prompt, force=force)
    targets = {t["label"]: t for t in configured_targets()}
    if decision.label in targets:
        t = targets[decision.label]
        try:
            return complete_http(
                prompt,
                base_url=t["base_url"],
                api_key=t.get("api_key"),
                model=t["model"],
                route_label=decision.label,
            )
        except Exception as e:
            mock = _mock_generate(prompt, RouteDecision("mock", f"provider_error:{e}", 15.0))
            mock["fallback_from"] = decision.label
            mock["provider_error"] = str(e)
            return mock
    return _mock_generate(prompt, decision)


def _mock_generate(prompt: str, decision: RouteDecision) -> dict:
    t0 = time.perf_counter()
    time.sleep(min(decision.simulated_latency_ms / 1000.0, 0.05))
    elapsed = (time.perf_counter() - t0) * 1000
    digest = hashlib.sha1(prompt.encode()).hexdigest()[:8]
    text = (
        f"[NEXUS {decision.label} router] "
        f"Acknowledged prompt ({len(prompt)} chars). "
        f"This is a local mock completion (id={digest}). "
        f"Route reason: {decision.reason}."
    )
    tokens_in = max(1, len(prompt.split()))
    tokens_out = max(1, len(text.split()))
    return {
        "text": text,
        "route": decision.label,
        "reason": decision.reason,
        "latency_ms": round(elapsed, 2),
        "ttft_ms": round(elapsed, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_per_sec": round(tokens_out / (elapsed / 1000.0), 2) if elapsed else None,
        "hardware": "cpu_local_mock",
        "note": "No GPU claimed. Latencies are local mock timings unless a provider env var is set.",
    }
