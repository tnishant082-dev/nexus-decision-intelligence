"""Retry + fallback helper for live HTTP providers."""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def with_retry(fn: Callable[[], T], retries: int = 2, fallback: Callable[[Exception], T] | None = None) -> T:
    last: Exception | None = None
    for _ in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — gateway wants the last error
            last = e
    if fallback and last is not None:
        return fallback(last)
    assert last is not None
    raise last
