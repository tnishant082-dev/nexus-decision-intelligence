# Roadmap

Only items that are still actually missing.

## Near-term (code-shaped, not claimed done)

1. Recapture Streamlit screenshots after UI changes (`screenshots/nexus/`).
2. True time-based churn labels (hide last N days of orders, predict next window).
3. Chunking experiments with measured recall on a larger policy corpus.
4. Optional NetworkX/Neo4j live rebuild job that **replaces** the committed 41/112 snapshot after a measured run.

## Shipped in 1.4

- GraphRAG snapshot (41 nodes / 112 edges) with NetworkX optional and Neo4j idle.
- Linear SAMPLE twin (inventory / delay / demand / price / promotion).
- Gold-set agent evaluation (6 cases) + heuristic guardrails.
- Inference queue, retry, mock fallback; copilot Monday brief MD/PDF.
- Quality command (freshness, schema drift, nulls, dupes).
- JSON memory; in-process week replay (Kafka idle).

## Shipped in 1.3

- Wilson 95% intervals on order-grain OTIF (network + warehouse). Wald remains in `data-science/modules/inference_stats.py` for comparison.
- HITL ledger status history (`proposed → accepted|rejected|done` with timestamps/notes), not only a request flag.

## Requires extra infrastructure (out of this repo until you run it)

- Ollama / vLLM / llama.cpp server process
- Neo4j
- Kafka / Redpanda
- Postgres + pgvector
- MLflow tracking server
- Prometheus + Grafana containers
- Airflow / Dagster scheduler
- OIDC

## Will not pretend

- Live OMS/WMS CDC
- GPU throughput leaderboards
- Statutory inventory accounting
- Network digital twin
