from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_hybrid_rag_has_citations():
    from ai.rag.retriever import retrieve

    hits = retrieve("OTIF escalation policy expedite")
    assert hits
    assert hits[0].get("citation") or hits[0].get("doc_id")


def test_rag_eval_recall():
    from ai.rag.evaluate import evaluate

    report = evaluate()
    assert report["n"] >= 3
    assert report["recall_at_k"] >= 0.5
    assert report["faithfulness"] is None
