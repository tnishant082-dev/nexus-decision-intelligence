"""Simple lexical RAG over docs/knowledge/*.md (no external embeddings required)."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parents[2] / "docs" / "knowledge"


@dataclass
class Chunk:
    doc_id: str
    title: str
    text: str
    score: float = 0.0


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_chunks(knowledge_dir: Path = KNOWLEDGE) -> list[Chunk]:
    chunks: list[Chunk] = []
    for p in sorted(knowledge_dir.glob("*.md")):
        raw = p.read_text()
        title = raw.splitlines()[0].lstrip("# ").strip() if raw else p.stem
        parts = re.split(r"\n(?=## )", raw)
        for i, part in enumerate(parts):
            part = part.strip()
            if len(part) < 40:
                continue
            chunks.append(Chunk(doc_id=f"{p.name}#sec{i}", title=title, text=part))
    return chunks


def retrieve(question: str, top_k: int = 3, knowledge_dir: Path = KNOWLEDGE) -> list[dict]:
    q = _tokenize(question)
    scored = []
    for ch in load_chunks(knowledge_dir):
        tokens = _tokenize(ch.text)
        if not tokens:
            continue
        overlap = len(q & tokens)
        score = overlap / (len(q) ** 0.5 + 1e-6)
        if score > 0:
            scored.append(Chunk(ch.doc_id, ch.title, ch.text, score))
    scored.sort(key=lambda c: c.score, reverse=True)
    return [
        {"doc_id": c.doc_id, "title": c.title, "snippet": c.text[:500], "score": round(c.score, 3)}
        for c in scored[:top_k]
    ]
