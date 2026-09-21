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


def test_ab_calculator():
    sys.path.insert(0, str(ROOT / "data-science" / "modules"))
    from ab_testing import two_proportion_ztest

    out = two_proportion_ztest(40, 100, 55, 100)
    assert "p_value" in out
    assert "limitations" in out
