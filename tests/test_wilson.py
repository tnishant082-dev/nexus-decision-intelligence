"""Wilson interval unit tests — no warehouse required."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data-science" / "modules"))

from decisions.wilson import wilson_interval as wilson_pct
from inference_stats import wilson_interval as wilson_frac


def test_wilson_network_otif_matches_console():
    # Order-grain OTIF on this extract: 26849 / 65752 = 40.83%
    w = wilson_pct(26849, 65752)
    assert w["center"] == 40.83
    assert w["lo"] == 40.46
    assert w["hi"] == 41.21
    assert w["n"] == 65752


def test_wilson_zero_n():
    w = wilson_pct(0, 0)
    assert w["n"] == 0
    assert w["lo"] is None


def test_wilson_matches_scipy_form():
    frac = wilson_frac(26849, 65752)
    pct = wilson_pct(26849, 65752)
    assert math.isclose(100 * frac["center"], pct["center"], abs_tol=0.015)
    assert math.isclose(100 * frac["ci_low"], pct["lo"], abs_tol=0.015)
    assert math.isclose(100 * frac["ci_high"], pct["hi"], abs_tol=0.015)
    assert frac["method"].startswith("Wilson")


def test_ledger_history(monkeypatch, tmp_path):
    from decisions import ledger

    monkeypatch.setattr(ledger, "LEDGER", tmp_path / "ledger.json")
    item = ledger.add("Wilson action", "test", 10.0, "ops")
    assert item["history"][0]["status"] == "proposed"
    updated = ledger.set_status(item["id"], "accepted", note="monday")
    assert updated["status"] == "accepted"
    assert updated["history"][-1]["note"] == "monday"
    assert len(updated["history"]) == 2
