# Deployment

This repository is a **local / Docker demo**, not a SaaS deploy guide.

## Prerequisites

- Python 3.11+
- ~1 GB disk for parquet + DuckDB
- Optional: Docker, Ollama, a Groq/OpenAI key

## Local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
export NEXUS_API_KEY=dev-nexus-key   # Windows: set NEXUS_API_KEY=dev-nexus-key

python data-engineering/run_pipeline.py
python -m ml.run_all                 # optional
uvicorn backend.main:app --port 8000
# other terminal
API_URL=http://127.0.0.1:8000 streamlit run frontend/streamlit_app.py
```

Change the default API key before any network bind that is not localhost.

## Docker

```bash
docker compose up --build
```

API `:8000`, UI `:8501`. Compose does **not** start vLLM, Ollama, Prometheus, or Grafana.

## Optional live LLM

Set one of:

- `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`, `OPENAI_MODEL`)
- `GROQ_API_KEY`
- `OLLAMA_BASE_URL=http://127.0.0.1:11434` (OpenAI-compatible `/v1` is appended)
- `VLLM_BASE_URL=http://127.0.0.1:8001/v1`
- `LLAMACPP_BASE_URL=http://127.0.0.1:8080/v1`
- `NEXUS_LLM_PROVIDER=openai|groq|ollama|vllm|llamacpp`

If the HTTP call fails, the gateway **falls back to mock** and records `provider_error`.

Cost fields stay `0` unless `NEXUS_USD_PER_1K_IN` / `NEXUS_USD_PER_1K_OUT` are set.

## Observability

- Scrape `GET /metrics`
- Example scrape config: `observability/prometheus.yml`
- Example Grafana dashboard: `observability/grafana/nexus-inference.json`
- Inference log: `monitoring/inference_logs.sqlite`
- Audit log: `monitoring/audit.sqlite` (when `NEXUS_AUDIT=1`)

## Roles

| Header | Effect |
|---|---|
| `X-API-Key` | Required for `/api/v1/*` |
| `X-Nexus-Role: viewer` (default) | KPIs + investigate; SQL console blocked |
| `analyst` / `admin` | SQL console allowed (still SELECT-only) |

## CI

`.github/workflows/ci.yml` installs `requirements.txt` (not optional extras), builds the warehouse, runs pytest.
