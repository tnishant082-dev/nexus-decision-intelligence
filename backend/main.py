
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

from backend.core.auth import require_api_key
from backend.core.config import API_KEY
from ai.agents.investigate import investigate
from ai.rag.retriever import retrieve
from ai.tools.sql_tool import run_sql
from inference.gateway import complete, stats as inference_stats
from ml.serving import predict as ml_predict

app = FastAPI(
    title="NEXUS Decision Intelligence Platform",
    description="Local-first retail + supply chain decision intelligence. Mock LLM default.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# naive in-memory rate limit
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
    return {"status": "ok", "service": "nexus", "llm_default": "mock"}

@app.get("/metrics")
def metrics():
    s = inference_stats()
    lines = [
        "# HELP nexus_inference_calls_total Total inference gateway calls",
        "# TYPE nexus_inference_calls_total counter",
        f'nexus_inference_calls_total {s.get("total_calls", 0)}',
    ]
    for row in s.get("by_route", []):
        lines.append(f'nexus_inference_route_calls{{route="{row["route"]}"}} {row["calls"]}')
        lines.append(f'nexus_inference_route_latency_ms{{route="{row["route"]}"}} {row["avg_latency_ms"]}')
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")

class InvestigateRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)

class SQLRequest(BaseModel):
    sql: str
    limit: int = 50

class CompleteRequest(BaseModel):
    prompt: str
    force: str | None = None
    use_cache: bool = True

class DemandRequest(BaseModel):
    rows: list[dict]

class RagRequest(BaseModel):
    question: str
    top_k: int = 3

@app.post("/api/v1/investigate")
def api_investigate(body: InvestigateRequest, _=Depends(require_api_key)):
    return investigate(body.question)

@app.post("/api/v1/sql")
def api_sql(body: SQLRequest, _=Depends(require_api_key)):
    return run_sql(body.sql, limit=body.limit)

@app.post("/api/v1/rag")
def api_rag(body: RagRequest, _=Depends(require_api_key)):
    return {"hits": retrieve(body.question, top_k=body.top_k)}

@app.post("/api/v1/inference/complete")
def api_complete(body: CompleteRequest, _=Depends(require_api_key)):
    return complete(body.prompt, force=body.force, use_cache=body.use_cache)

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

@app.get("/api/v1/kpis")
def api_kpis(_=Depends(require_api_key)):
    exec_ = run_sql("SELECT * FROM v_exec_kpis")
    otif = run_sql("SELECT * FROM v_otif_order")
    logistics = run_sql("SELECT * FROM v_logistics")
    return {
        "executive": exec_.get("rows", [{}])[0] if exec_.get("ok") else {},
        "otif": otif.get("rows", [{}])[0] if otif.get("ok") else {},
        "logistics": logistics.get("rows", [{}])[0] if logistics.get("ok") else {},
        "source": "duckdb warehouse over DataCo + Online Retail II extracts",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
