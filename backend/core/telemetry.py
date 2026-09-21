"""Optional OpenTelemetry — no-op if SDK missing."""
from __future__ import annotations


def instrument_app(app) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        return
