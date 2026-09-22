from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_investigate_graph_and_human_review():
    from ai.agents.investigate import investigate

    r = investigate("Why is OTIF low?", human_review=True)
    assert r["drivers"]
    assert r["pending_review"] is True
    assert r["recommendations"][0].startswith("HUMAN REVIEW")
    agents = {e.get("agent") for e in r["agent_trail"]}
    assert "analytics" in agents
    assert "decision" in agents
    assert r["citations"] is not None


def test_action_cards_keep_the_extract_window_and_metric_meaning():
    from ai.agents.nodes import decision_agent

    state = decision_agent({
        "question": "Why is OTIF low and what should we do about late-line revenue?",
        "documents": [{"title": "OTIF policy", "doc_id": "01_otif_policy"}],
        "inventory_notes": [],
        "risk_notes": ["180d churn proxy 12%; avg LTV $40"],
        "human_review": False,
        "trail": [],
    })
    cards = state["action_cards"]
    assert cards
    assert len(cards) == len(state["recommendations"])
    for card in cards:
        assert card["extract_window"] == "2015-01-01 → 2018-01-31"
        assert card["means"]
        assert card["does_not_mean"]
        assert card["held"] is False
    late = [card for card in cards if card["metric_id"] == "late_revenue"]
    assert late
    assert "lost sales" in late[0]["does_not_mean"].lower()
    assert "exposure" in late[0]["means"].lower()
    churn = [card for card in cards if card["metric_id"] == "churn_proxy"]
    assert churn
    assert "contracted churn" in churn[0]["does_not_mean"].lower()


def test_ab_calculator():
    sys.path.insert(0, str(ROOT / "data-science" / "modules"))
    from ab_testing import two_proportion_ztest

    out = two_proportion_ztest(40, 100, 55, 100)
    assert "p_value" in out
    assert "limitations" in out
