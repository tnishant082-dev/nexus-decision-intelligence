# Roadmap

Only items that are still actually missing.

## Near-term (code-shaped, not claimed done)

1. Recapture Streamlit screenshots after UI changes (`screenshots/nexus/`).
2. True time-based churn labels (hide last N days of orders, predict next window).
3. Chunking experiments with measured recall on a larger policy corpus.

## Shipped in 1.3

- Wilson 95% intervals on order-grain OTIF (network + warehouse). Wald remains in `data-science/modules/inference_stats.py` for comparison.
- HITL ledger status history (`proposed → accepted|rejected|done` with timestamps/notes), not only a request flag.

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
