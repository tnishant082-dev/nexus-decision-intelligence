"""SQL metric views + dictionary tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"


@pytest.fixture(scope="module")
def con():
    if not DB.exists():
        pytest.skip("warehouse missing")
    import duckdb

    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()


def test_dictionary_covers_required_kpis():
    data = yaml.safe_load((ROOT / "analytics" / "metrics" / "dictionary.yaml").read_text())
    names = set(data["metrics"])
    for key in ("revenue", "profit", "margin", "growth", "otif", "fill_rate", "perfect_order",
                "inventory_turns", "coverage", "stockout_risk", "retention", "churn", "lifetime_value"):
        assert key in names


@pytest.mark.skipif(not DB.exists(), reason="warehouse missing")
def test_metric_views(con):
    for view in ("v_exec_kpis", "v_otif_order", "v_fill_rate", "v_inventory_kpis", "v_customer_kpis", "v_finance_growth"):
        n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        assert n >= 1, view
    row = con.execute("SELECT revenue_m, profit_m, margin_pct FROM v_exec_kpis").fetchone()
    assert row[0] > 0
    otif = con.execute("SELECT otif_pct, perfect_order_pct FROM v_otif_order").fetchone()
    assert 0 <= otif[0] <= 100
    fill = con.execute("SELECT fill_rate_pct FROM v_fill_rate").fetchone()[0]
    assert 0 <= fill <= 100
