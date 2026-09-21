"""Multi-agent investigate flow (graph orchestration)."""
from __future__ import annotations

from datetime import datetime, timezone

from ai.agents.graph import run_graph
from decisions.economics import value_at_stake, warehouse_exceptions


def investigate(question: str, human_review: bool = False) -> dict:
    from security.guardrails.scan import scan

    g = scan(question, "agent")
    if not g["allowed"]:
        return {
            "question": question,
            "blocked": True,
            "findings": g["findings"],
            "drivers": ["Blocked by guardrails."],
            "recommendations": [],
            "citations": [],
            "agent_trail": [{"agent": "guardrails", "note": "blocked"}],
        }
    state = run_graph(question, human_review=human_review)
    sql_results = state.get("sql_results") or []
    docs = state.get("documents") or []
    models = state.get("models") or []
    vas = value_at_stake()
    top_exc = warehouse_exceptions(limit=3)
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
    recs.append(
        f"Value at stake: ${vas['late_revenue']:,.0f} late-line revenue "
        f"({vas['late_revenue_share_pct']}% of sales); OTIF {vas['actual_otif_pct']}% vs SAMPLE {vas['sample_otif_target_pct']}%."
    )
    if top_exc:
        recs.append(
            f"Largest $ late pool: {top_exc[0]['warehouse_name']} (${top_exc[0]['late_revenue']:,.0f})."
        )
    if state.get("pending_review"):
        recs = ["HUMAN REVIEW: recommendations held until an operator approves."] + recs
    return {
        "question": question,
        "drivers": state.get("drivers") or [],
        "recommendations": recs,
        "value_at_stake": {
            "late_revenue": vas["late_revenue"],
            "late_revenue_share_pct": vas["late_revenue_share_pct"],
            "delay_cost": vas["delay_cost"],
            "expedite_freight": vas["expedite_freight"],
            "otif_gap_pp": vas["otif_gap_pp"],
            "yoy_2016_2017": vas.get("yoy_2016_2017"),
        },
        "priority_exceptions": top_exc,
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
            "Local NEXUS demo. Late revenue is service-risk exposure, not proven lost sales. "
            "Policies are SAMPLE; LLM is mock unless a provider is configured."
        ),
    }
