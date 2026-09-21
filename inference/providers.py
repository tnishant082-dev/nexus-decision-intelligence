"""OpenAI-compatible HTTP completion (covers OpenAI, Groq, vLLM, Ollama, llama.cpp server)."""
from __future__ import annotations

import os
import time
from typing import Any

import httpx


def complete_http(
    prompt: str,
    *,
    base_url: str,
    api_key: str | None,
    model: str,
    route_label: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": int(os.getenv("NEXUS_MAX_TOKENS", "256")),
        "temperature": 0.2,
    }
    t0 = time.perf_counter()
    ttft_ms = None
    text = ""
    usage = {}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=headers, json=payload)
        ttft_ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        data = r.json()
    elapsed = (time.perf_counter() - t0) * 1000
    choices = data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        text = msg.get("content") or choices[0].get("text") or ""
    usage = data.get("usage") or {}
    tokens_in = int(usage.get("prompt_tokens") or max(1, len(prompt.split())))
    tokens_out = int(usage.get("completion_tokens") or max(1, len(text.split())))
    return {
        "text": text,
        "route": route_label,
        "reason": f"http:{base_url}",
        "latency_ms": round(elapsed, 2),
        "ttft_ms": round(ttft_ms or elapsed, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_per_sec": round(tokens_out / (elapsed / 1000.0), 2) if elapsed else None,
        "hardware": "remote_http",
        "model": model,
        "provider_usage": usage,
        "note": "Live HTTP completion. Cost uses configured USD rates; 0 if unset.",
    }


def configured_targets() -> list[dict[str, str]]:
    targets = []
    if os.getenv("OPENAI_API_KEY"):
        targets.append({
            "label": "openai",
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        })
    if os.getenv("GROQ_API_KEY"):
        targets.append({
            "label": "groq",
            "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            "api_key": os.getenv("GROQ_API_KEY", ""),
            "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        })
    if os.getenv("OLLAMA_BASE_URL"):
        targets.append({
            "label": "ollama",
            "base_url": os.getenv("OLLAMA_BASE_URL").rstrip("/") + "/v1",
            "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        })
    if os.getenv("VLLM_BASE_URL"):
        targets.append({
            "label": "vllm",
            "base_url": os.getenv("VLLM_BASE_URL").rstrip("/"),
            "api_key": os.getenv("VLLM_API_KEY", "EMPTY"),
            "model": os.getenv("VLLM_MODEL", "local-model"),
        })
    if os.getenv("LLAMACPP_BASE_URL"):
        targets.append({
            "label": "llamacpp",
            "base_url": os.getenv("LLAMACPP_BASE_URL").rstrip("/"),
            "api_key": os.getenv("LLAMACPP_API_KEY", "EMPTY"),
            "model": os.getenv("LLAMACPP_MODEL", "local-model"),
        })
    return targets
