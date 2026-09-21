# Roadmap

Only items that are still actually missing.

## Near-term (code-shaped, not claimed done)

1. Recapture Streamlit screenshots after UI changes (`screenshots/nexus/`).
2. Wilson intervals for OTIF proportion CIs.
3. True time-based churn labels (hide last N days of orders, predict next window).
4. Human-in-the-loop persist (approve/reject table) instead of a request flag.
5. Chunking experiments with measured recall on a larger policy corpus.

## Requires extra infrastructure (out of this repo until you run it)

- Ollama / vLLM / llama.cpp server process
- Postgres + pgvector
- MLflow tracking server
- Prometheus + Grafana containers
- Airflow / Dagster scheduler
- OIDC

## Will not pretend

- Live OMS/WMS CDC
- GPU throughput leaderboards
- Statutory inventory accounting
