from __future__ import annotations

from fastapi.testclient import TestClient


def test_sql_guard_with_analyst_role(client=None):
    from backend.main import app

    c = TestClient(app)
    r = c.post(
        "/api/v1/sql",
        json={"sql": "DELETE FROM fact_orders"},
        headers={"X-API-Key": "dev-nexus-key", "X-Nexus-Role": "analyst"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_kpis_extended():
    from backend.main import app

    c = TestClient(app)
    r = c.get("/api/v1/kpis", headers={"X-API-Key": "dev-nexus-key"})
    assert r.status_code == 200
    body = r.json()
    assert "fill" in body
    assert "inventory" in body
    assert "customer" in body


def test_metrics_prometheus_cache():
    from backend.main import app

    c = TestClient(app)
    r = c.get("/metrics")
    assert "nexus_inference_cache_hit_rate" in r.text
