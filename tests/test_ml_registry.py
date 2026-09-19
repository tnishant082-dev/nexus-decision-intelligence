"""ML registry smoke — verifies registered forecast artifact loads."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REG = ROOT / "ml" / "registry" / "demand_forecast_v1.json"


@pytest.mark.skipif(not REG.exists(), reason="forecast registry missing")
def test_forecast_registry_points_to_model():
    meta = json.loads(REG.read_text())
    path = Path(meta["metrics"]["model_path"])
    if not path.is_absolute():
        path = ROOT / path
    assert path.exists(), path
    assert meta.get("model_id") == "demand_forecast_v1"
