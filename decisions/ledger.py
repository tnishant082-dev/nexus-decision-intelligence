"""Persisted accept/reject ledger for recommended actions (local JSON)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "monitoring" / "decision_ledger.json"


def _load() -> list[dict]:
    if not LEDGER.exists():
        return []
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save(rows: list[dict]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def add(title: str, rationale: str, dollars: float | None, owner: str, source: str = "console") -> dict:
    rows = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "rationale": rationale,
        "dollars_at_stake": dollars,
        "owner": owner,
        "status": "proposed",
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "history": [{"status": "proposed", "at": datetime.now(timezone.utc).isoformat(), "note": None}],
    }
    rows.append(item)
    _save(rows)
    return item


def set_status(item_id: str, status: str, note: str | None = None) -> dict | None:
    if status not in {"proposed", "accepted", "rejected", "done"}:
        raise ValueError("status must be proposed|accepted|rejected|done")
    rows = _load()
    found = None
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if row["id"] == item_id:
            row["status"] = status
            row["updated_at"] = now
            hist = list(row.get("history") or [])
            hist.append({"status": status, "at": now, "note": note})
            row["history"] = hist
            found = row
    _save(rows)
    return found


def list_items() -> list[dict]:
    return _load()
