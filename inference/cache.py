"""Simple response cache keyed by route+prompt hash."""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache"

def _key(route: str, prompt: str) -> str:
    return hashlib.sha256(f"{route}::{prompt}".encode()).hexdigest()

def get(route: str, prompt: str) -> dict | None:
    path = CACHE_DIR / f"{_key(route, prompt)}.json"
    if path.exists():
        data = json.loads(path.read_text())
        data["cache_hit"] = True
        return data
    return None

def put(route: str, prompt: str, response: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = dict(response)
    payload["cached_at"] = time.time()
    payload["cache_hit"] = False
    (CACHE_DIR / f"{_key(route, prompt)}.json").write_text(json.dumps(payload, indent=2))
