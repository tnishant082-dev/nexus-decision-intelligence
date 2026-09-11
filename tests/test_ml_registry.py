
"""ML training smoke tests — may be slow; marked as integration-ish."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"

@pytest.mark.skipif(not DB.exists(), reason="warehouse missing")
def test_forecast_train_smoke():
    from ml.train_forecast import train
    m = train()
    assert m["test_rows"] > 0
    assert "mae" in m
    assert (ROOT / "ml" / "registry" / "demand_forecast_v1.json").exists()
