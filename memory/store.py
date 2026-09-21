"""Local JSON memory of incidents / investigations / actions / recommendations.

Not a hosted incident store. Customer names are not stored.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "artifacts" / "memory.json"

SEED = [
    {
        "id": "inc-otif-extract",
        "kind": "incident",
        "at": "2017-12-01T00:00:00Z",
        "title": "Network OTIF far below SAMPLE 92% across the extract",
        "body": "Order-grain OTIF 40.83% (Wilson 40.46–41.21, n=65752). Late-line revenue is 55%+ of sales. Not a live incident clock — extract window 2015–2018.",
        "tags": ["otif", "service"],
    },
    {
        "id": "inv-europe-late",
        "kind": "investigation",
        "at": "2018-01-15T00:00:00Z",
        "title": "Europe RDC concentrates late-line $",
        "body": "Highest late-$ warehouse is Europe RDC. Split late vs short-ship; First Class late rate 95%.",
        "tags": ["otif", "warehouse", "europe"],
    },
    {
        "id": "act-fan-shop",
        "kind": "action",
        "at": "2018-01-20T00:00:00Z",
        "title": "Score Fan Shop as primary late-$ supplier",
        "body": "GraphRAG: Fan Shop ~$8.4M late-line, preferred vendor, medium risk tier, 4-day SAMPLE SLA. Dual-source plan is SAMPLE vendor policy for high exposure.",
        "tags": ["supplier", "fan-shop", "otif"],
    },
    {
        "id": "rec-coverage",
        "kind": "recommendation",
        "at": "2018-01-22T00:00:00Z",
        "title": "Do not cut inventory to chase OTIF without a late/short-ship split",
        "body": "Coverage ratios sit in SAMPLE yellow/red working-capital bands while OTIF is ~41%. Cash vs service tradeoff.",
        "tags": ["inventory", "otif"],
    },
]


def _load(path: Path | None = None) -> list[dict]:
    p = path or STORE
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(SEED, indent=2))
        return list(SEED)
    return json.loads(p.read_text())


def seed(path: Path | None = None) -> list[dict]:
    p = path or STORE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(SEED, indent=2))
    return list(SEED)


def add(kind: str, title: str, body: str, tags: list[str] | None = None, path: Path | None = None) -> dict:
    p = path or STORE
    items = _load(p)
    row = {
        "id": uuid.uuid4().hex[:8],
        "kind": kind,
        "at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "body": body,
        "tags": tags or [],
    }
    items.insert(0, row)
    p.write_text(json.dumps(items, indent=2))
    return row


def search(question: str, path: Path | None = None) -> list[dict]:
    terms = [t for t in question.lower().split() if len(t) > 2]
    scored = []
    for m in _load(path):
        hay = f"{m['title']} {m['body']} {' '.join(m.get('tags') or [])}".lower()
        score = sum(1 for t in terms if t in hay)
        if score:
            scored.append((score, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]
