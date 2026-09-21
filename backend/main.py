"""NEXUS Decision Intelligence — FastAPI backend."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.audit import log as audit_log
from backend.core.auth import optional_role, require_api_key
from backend.core.config import AUDIT_ENABLED, CORS_ORIGINS
from backend.core.telemetry import instrument_app
from ai.agents.investigate import investigate
from ai.rag.retriever import retrieve
from ai.tools.sql_tool import run_sql
from inference.gateway import complete, complete_batch, stats as inference_stats
from ml.serving import predict as ml_predict

app = FastAPI(
    title="NEXUS Decision Intelligence Platform",
    description="Local-first retail + supply chain decision intelligence. Mock LLM default.",
    version="1.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://127.0.0.1:8501"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
instrument_app(app)

_BUCKET: dict[str, list[float]] = {}
RATE_PER_MIN = 60


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        key = request.headers.get("X-API-Key", request.client.host if request.client else "anon")
        now = time.time()
        window = _BUCKET.setdefault(key, [])
        _BUCKET[key] = [t for t in window if now - t < 60]
        if len(_BUCKET[key]) >= RATE_PER_MIN:
            return PlainTextResponse("Rate limit exceeded", status_code=429)
        _BUCKET[key].append(now)
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nexus", "llm_default": "mock", "version": "1.2.0"}


@app.get("/metrics")
def metrics():
    s = inference_stats()
    lines = [
        "# HELP nexus_inference_calls_total Total inference gateway calls",
        "# TYPE nexus_inference_calls_total counter",
        f'nexus_inference_calls_total {s.get("total_calls", 0)}',
        "# HELP nexus_inference_cache_hit_rate Cache hit rate",
        "# TYPE nexus_inference_cache_hit_rate gauge",
        f'nexus_inference_cache_hit_rate {s.get("cache_hit_rate", 0)}',
    ]
    for row in s.get("by_route", []):
        route = row["route"]
        lines.append(f'nexus_inference_route_calls{{route="{route}"}} {row["calls"]}')
        lines.append(f'nexus_inference_route_latency_ms{{route="{route}"}} {row["avg_latency_ms"]}')
        if row.get("avg_ttft_ms") is not None:
            lines.append(f'nexus_inference_route_ttft_ms{{route="{route}"}} {row["avg_ttft_ms"]}')
        if row.get("avg_tokens_per_sec") is not None:
            lines.append(f'nexus_inference_route_tokens_per_sec{{route="{route}"}} {row["avg_tokens_per_sec"]}')
        if row.get("cost_usd") is not None:
            lines.append(f'nexus_inference_route_cost_usd{{route="{route}"}} {row["cost_usd"]}')
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")


class InvestigateRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    human_review: bool = False


class SQLRequest(BaseModel):
    sql: str
    limit: int = 50


class CompleteRequest(BaseModel):
    prompt: str
    force: str | None = None
    use_cache: bool = True


class BatchCompleteRequest(BaseModel):
    prompts: list[str]
    force: str | None = None


class DemandRequest(BaseModel):
    rows: list[dict]


class RagRequest(BaseModel):
    question: str
    top_k: int = 3


@app.post("/api/v1/investigate")
def api_investigate(body: InvestigateRequest, key=Depends(require_api_key), role=Depends(optional_role)):
    if AUDIT_ENABLED:
        audit_log("investigate", key[:6], {"role": role, "q": body.question[:80]})
    return investigate(body.question, human_review=body.human_review)


@app.post("/api/v1/sql")
def api_sql(body: SQLRequest, key=Depends(require_api_key), role=Depends(optional_role)):
    if role == "viewer":
        return {"ok": False, "error": "SQL console requires analyst or admin role (X-Nexus-Role)."}
    if AUDIT_ENABLED:
        audit_log("sql", key[:6], {"role": role})
    return run_sql(body.sql, limit=body.limit)


@app.post("/api/v1/rag")
def api_rag(body: RagRequest, _=Depends(require_api_key)):
    hits = retrieve(body.question, top_k=body.top_k)
    return {"hits": hits, "citations": [h.get("citation") or h.get("doc_id") for h in hits]}


@app.post("/api/v1/inference/complete")
def api_complete(body: CompleteRequest, _=Depends(require_api_key)):
    return complete(body.prompt, force=body.force, use_cache=body.use_cache)


@app.post("/api/v1/inference/batch")
def api_batch(body: BatchCompleteRequest, _=Depends(require_api_key)):
    return {"results": complete_batch(body.prompts, force=body.force)}


@app.get("/api/v1/inference/stats")
def api_inf_stats(_=Depends(require_api_key)):
    return inference_stats()


@app.post("/api/v1/ml/forecast")
def api_forecast(body: DemandRequest, _=Depends(require_api_key)):
    try:
        return {"predictions": ml_predict.predict_demand(body.rows)}
    except FileNotFoundError as e:
        return {"error": "Model not trained yet. Run: python -m ml.run_all", "detail": str(e)}


@app.post("/api/v1/ml/anomaly")
def api_anomaly(body: DemandRequest, _=Depends(require_api_key)):
    try:
        return {"scores": ml_predict.score_anomaly(body.rows)}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/ml/churn")
def api_churn(body: DemandRequest, _=Depends(require_api_key)):
    try:
        return {"predictions": ml_predict.predict_churn(body.rows)}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/ml/stockout")
def api_stockout(body: DemandRequest, _=Depends(require_api_key)):
    try:
        return {"predictions": ml_predict.predict_stockout(body.rows)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/kpis")
def api_kpis(_=Depends(require_api_key)):
    def first(sql: str) -> dict:
        r = run_sql(sql)
        return r.get("rows", [{}])[0] if r.get("ok") and r.get("rows") else {}

    return {
        "executive": first("SELECT * FROM v_exec_kpis"),
        "otif": first("SELECT * FROM v_otif_order"),
        "fill": first("SELECT * FROM v_fill_rate"),
        "logistics": first("SELECT * FROM v_logistics"),
        "inventory": first("SELECT * FROM v_inventory_kpis"),
        "customer": first("SELECT * FROM v_customer_kpis"),
        "growth": run_sql("SELECT * FROM v_finance_growth").get("rows") if run_sql("SELECT * FROM v_finance_growth").get("ok") else [],
        "source": "duckdb warehouse over DataCo + Online Retail II extracts",
    }


class ScenarioRequest(BaseModel):
    warehouse_name: str | None = None
    close_pct: float = 0.25
    expedite_cut_pct: float = 0.3


class LedgerAdd(BaseModel):
    title: str
    rationale: str = ""
    dollars_at_stake: float | None = None
    owner: str = "ops"


class LedgerStatus(BaseModel):
    id: str
    status: str


@app.get("/api/v1/value-at-stake")
def api_vas(_=Depends(require_api_key)):
    from decisions.economics import carrier_exceptions, value_at_stake, warehouse_exceptions

    return {
        "summary": value_at_stake(),
        "warehouse_exceptions": warehouse_exceptions(),
        "carrier_exceptions": carrier_exceptions(),
    }


@app.post("/api/v1/scenarios/late-gap")
def api_scenario_late(body: ScenarioRequest, _=Depends(require_api_key)):
    from decisions.scenarios import close_late_gap

    return close_late_gap(warehouse_name=body.warehouse_name, close_pct=body.close_pct)


@app.post("/api/v1/scenarios/expedite")
def api_scenario_exp(body: ScenarioRequest, _=Depends(require_api_key)):
    from decisions.scenarios import cut_expedite

    return cut_expedite(cut_pct=body.expedite_cut_pct)


@app.get("/api/v1/brief.md")
def api_brief(_=Depends(require_api_key)):
    from decisions.brief import build_brief

    return PlainTextResponse(build_brief(), media_type="text/markdown")


@app.get("/api/v1/ledger")
def api_ledger_list(role=Depends(optional_role), _=Depends(require_api_key)):
    from decisions.ledger import list_items

    return {"items": list_items(), "role": role}


@app.post("/api/v1/ledger")
def api_ledger_add(body: LedgerAdd, key=Depends(require_api_key), role=Depends(optional_role)):
    from decisions.ledger import add

    if role == "viewer":
        return {"ok": False, "error": "analyst or admin role required"}
    item = add(body.title, body.rationale, body.dollars_at_stake, body.owner, source="api")
    if AUDIT_ENABLED:
        audit_log("ledger_add", key[:6], {"id": item["id"]})
    return item


@app.post("/api/v1/ledger/status")
def api_ledger_status(body: LedgerStatus, key=Depends(require_api_key), role=Depends(optional_role)):
    from decisions.ledger import set_status

    if role == "viewer":
        return {"ok": False, "error": "analyst or admin role required"}
    item = set_status(body.id, body.status)
    if AUDIT_ENABLED:
        audit_log("ledger_status", key[:6], {"id": body.id, "status": body.status})
    return item or {"ok": False, "error": "not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
