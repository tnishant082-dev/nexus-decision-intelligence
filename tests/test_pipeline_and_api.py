
"""Pytest suite — mock path must stay green without external APIs."""
from __future__ import annotations
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"


@pytest.fixture(scope="session", autouse=True)
def ensure_warehouse():
    if not DB.exists():
        sys.path.insert(0, str(ROOT / "data-engineering"))
        from etl.land import land
        from etl.clean import clean
        from etl.warehouse import load_warehouse
        land()
        clean()
        load_warehouse()
    assert DB.exists()


@pytest.fixture(scope="module")
def client():
    from backend.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required(client):
    r = client.post("/api/v1/investigate", json={"question": "Why is OTIF low?"})
    assert r.status_code == 401


def test_investigate(client):
    r = client.post(
        "/api/v1/investigate",
        json={"question": "Why is OTIF low and which warehouses are late?"},
        headers={"X-API-Key": "dev-nexus-key"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "drivers" in body and "recommendations" in body and "evidence" in body
    assert body["llm_mode"] == "mock"
    assert body["confidence"] > 0


def test_kpis(client):
    r = client.get("/api/v1/kpis", headers={"X-API-Key": "dev-nexus-key"})
    assert r.status_code == 200
    body = r.json()
    assert body["executive"].get("revenue_m", 0) > 0
    assert body["otif"].get("otif_pct", 0) > 0


def test_sql_readonly(client):
    r = client.post(
        "/api/v1/sql",
        json={"sql": "DELETE FROM fact_orders"},
        headers={"X-API-Key": "dev-nexus-key"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_rag():
    from ai.rag.retriever import retrieve
    hits = retrieve("OTIF escalation policy expedite")
    assert len(hits) >= 1


def test_inference_router():
    from inference.gateway import complete, stats
    r = complete("What is OTIF?", force="mock", use_cache=False)
    assert r["route"] == "mock"
    assert r["hardware"] == "cpu_local_mock"
    assert stats()["total_calls"] >= 1


def test_hypothesis_module():
    import importlib.util
    path = ROOT / "data-science" / "modules" / "eda_summary.py"
    spec = importlib.util.spec_from_file_location("eda_summary", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    report = mod.run()
    assert "p_value" in report
    assert report["n_late"] > 0


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "nexus_inference_calls_total" in r.text
