from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"


def test_value_at_stake_and_exceptions():
    from decisions.economics import value_at_stake, warehouse_exceptions

    v = value_at_stake()
    assert v["revenue"] > 0
    assert v["late_revenue"] > 0
    assert v["late_revenue"] < v["revenue"]
    assert v["late_revenue_share_pct"] > 10
    assert v["otif_gap_pp"] > 0
    yoy = v["yoy_2016_2017"]
    assert yoy["delta_m"] < 0
    rows = warehouse_exceptions(limit=3)
    assert rows and rows[0]["late_revenue"] >= rows[-1]["late_revenue"]


def test_scenario_is_linear_and_honest():
    from decisions.scenarios import close_late_gap

    r = close_late_gap(close_pct=0.25)
    assert r["ok"]
    assert abs(r["service_risk_addressed"] - r["late_revenue_pool"] * 0.25) < 1.0
    assert any("not" in x.lower() or "Does not" in x for x in r["limitations"])


def test_brief_and_ledger(monkeypatch):
    from decisions import ledger
    from decisions.brief import build_brief

    path = Path(__file__).resolve().parent / "_ledger_test.json"
    monkeypatch.setattr(ledger, "LEDGER", path)
    try:
        md = build_brief()
        assert "late" in md.lower()
        item = ledger.add("Test action", "unit test", 100.0, "ops")
        assert ledger.set_status(item["id"], "accepted")["status"] == "accepted"
    finally:
        if path.exists():
            path.unlink()


def test_investigate_attaches_dollars(client=None):
    from ai.agents.investigate import investigate

    r = investigate("Why did revenue decline and why is OTIF low?")
    assert "value_at_stake" in r
    assert r["value_at_stake"]["late_revenue"] > 0
    assert r["priority_exceptions"]
