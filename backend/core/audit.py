"""Append-only audit log (SQLite)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "monitoring" / "audit.sqlite"


def log(action: str, actor: str, detail: dict | None = None) -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, action TEXT, actor TEXT, detail TEXT
        )"""
    )
    con.execute(
        "INSERT INTO audit (ts, action, actor, detail) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), action, actor, json.dumps(detail or {})),
    )
    con.commit()
    con.close()
