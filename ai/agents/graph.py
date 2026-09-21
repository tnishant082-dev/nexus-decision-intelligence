"""Investigate orchestration: LangGraph when installed, otherwise a local linear graph with retries."""
from __future__ import annotations

from typing import Any, Callable

from ai.agents.nodes import (
    analytics_agent,
    decision_agent,
    forecast_agent,
    inventory_agent,
    rag_agent,
    risk_agent,
)


def _local_invoke(question: str, human_review: bool, max_retries: int = 2) -> dict[str, Any]:
    state: dict[str, Any] = {
        "question": question,
        "human_review": human_review,
        "trail": [{"agent": "orchestrator", "action": "plan", "backend": "local_graph"}],
        "retries": 0,
        "errors": [],
    }
    steps: list[Callable[[dict], dict]] = [
        analytics_agent,
        forecast_agent,
        inventory_agent,
        risk_agent,
        rag_agent,
        decision_agent,
    ]
    for step in steps:
        for attempt in range(max_retries):
            try:
                state = step(state)
                break
            except Exception as e:
                state["retries"] = int(state.get("retries") or 0) + 1
                state.setdefault("errors", []).append(f"{step.__name__}: {e}")
                state.setdefault("trail", []).append(
                    {"agent": "orchestrator", "action": "retry", "step": step.__name__, "attempt": attempt + 1}
                )
    return state


def _langgraph_invoke(question: str, human_review: bool) -> dict[str, Any] | None:
    try:
        from langgraph.graph import END, START, StateGraph  # type: ignore
    except Exception:
        return None

    from ai.agents.state import InvestigateState

    g = StateGraph(InvestigateState)
    g.add_node("analytics", analytics_agent)
    g.add_node("forecast", forecast_agent)
    g.add_node("inventory", inventory_agent)
    g.add_node("risk", risk_agent)
    g.add_node("rag", rag_agent)
    g.add_node("decision", decision_agent)
    g.add_edge(START, "analytics")
    g.add_edge("analytics", "forecast")
    g.add_edge("forecast", "inventory")
    g.add_edge("inventory", "risk")
    g.add_edge("risk", "rag")
    g.add_edge("rag", "decision")
    g.add_edge("decision", END)
    app = g.compile()
    result = app.invoke({"question": question, "human_review": human_review, "trail": [
        {"agent": "orchestrator", "action": "plan", "backend": "langgraph"}
    ]})
    return dict(result)


def run_graph(question: str, human_review: bool = False) -> dict[str, Any]:
    lg = _langgraph_invoke(question, human_review)
    if lg is not None:
        return lg
    return _local_invoke(question, human_review)
