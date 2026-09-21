"""Multi-agent investigate flow (graph orchestration)."""
from __future__ import annotations

from datetime import datetime, timezone

from ai.agents.graph import run_graph


def investigate(question: str, human_review: bool = False) -> dict:
    state = run_graph(question, human_review=human_review)
    sql_results = state.get("sql_results") or []
    docs = state.get("documents") or []
    models = state.get("models") or []
    conf = 0.35
    conf += 0.15 * min(len(sql_results), 3)
    conf += 0.1 * min(len(docs), 2)
    conf += 0.1 if models else 0
    conf = round(min(conf, 0.9), 2)
    backend = "local_graph"
    for ev in state.get("trail") or []:
        if ev.get("backend"):
            backend = ev["backend"]
            break
    recs = state.get("recommendations") or []
    if state.get("pending_review"):
        recs = ["HUMAN REVIEW: recommendations held until an operator approves."] + recs
    return {
        "question": question,
        "drivers": state.get("drivers") or [],
        "recommendations": recs,
        "evidence": {
            "sql": sql_results,
            "models": models,
            "documents": docs,
            "inventory": state.get("inventory_notes") or [],
            "risk": state.get("risk_notes") or [],
        },
        "citations": [d.get("citation") or d.get("doc_id") for d in docs],
        "agent_trail": state.get("trail") or [],
        "orchestration": backend,
        "pending_review": bool(state.get("pending_review")),
        "retries": state.get("retries") or 0,
        "errors": state.get("errors") or [],
        "confidence": conf,
        "llm_mode": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Local NEXUS demo. Metrics from DuckDB warehouse over public extracts; "
            "policies are SAMPLE docs; LLM responses are template/mock unless a provider key is configured."
        ),
    }
