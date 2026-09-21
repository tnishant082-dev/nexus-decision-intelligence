"""In-process request queue. Sequential by default (concurrency=1)."""
from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Callable, TypeVar

T = TypeVar("T")

_lock = Lock()
_q: deque = deque()
_inflight = 0
MAX_CONCURRENCY = 1


def enqueue(fn: Callable[[], T]) -> T:
    """Run fn under a process-local mutex so completes don't overlap."""
    global _inflight
    with _lock:
        _inflight += 1
        depth = _inflight
    try:
        result = fn()
        if isinstance(result, dict):
            result = dict(result)
            result["queue_depth"] = depth
        return result
    finally:
        with _lock:
            _inflight = max(0, _inflight - 1)
