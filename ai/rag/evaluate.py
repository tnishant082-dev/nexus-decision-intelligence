"""Offline RAG retrieval evaluation (no LLM faithfulness claims without a judge)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ai.rag.retriever import retrieve

CASES = Path(__file__).resolve().parent / "eval_cases.json"
OUT = Path(__file__).resolve().parents[2] / "ai" / "rag" / "last_eval.json"


def _doc_match(hit_id: str, relevant: list[str]) -> bool:
    return any(r in hit_id for r in relevant)


def evaluate(top_k: int = 3) -> dict:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    rows = []
    hits_at_k = 0
    term_hits = 0
    for case in cases:
        retrieved = retrieve(case["question"], top_k=top_k)
        rel = [_doc_match(h.get("doc_id", ""), case["relevant_doc_ids"]) for h in retrieved]
        hit = any(rel)
        hits_at_k += int(hit)
        blob = " ".join(h.get("snippet", "") for h in retrieved)
        terms_ok = all(re.search(t, blob, re.I) for t in case.get("must_include_terms", []))
        term_hits += int(terms_ok)
        precision = sum(rel) / max(len(retrieved), 1)
        rows.append({
            "id": case["id"],
            "hit_at_k": hit,
            "precision_at_k": round(precision, 3),
            "term_overlap_ok": terms_ok,
            "citations": [h.get("citation") or h.get("doc_id") for h in retrieved],
        })
    n = len(cases)
    report = {
        "n": n,
        "recall_at_k": round(hits_at_k / n, 4) if n else None,
        "mean_precision_at_k": round(sum(r["precision_at_k"] for r in rows) / n, 4) if n else None,
        "term_hit_rate": round(term_hits / n, 4) if n else None,
        "k": top_k,
        "cases": rows,
        "faithfulness": None,
        "answer_relevance": None,
        "note": "Faithfulness and answer relevance require an LLM judge or human labels. This harness scores retrieval recall/precision against gold doc ids only.",
    }
    OUT.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
