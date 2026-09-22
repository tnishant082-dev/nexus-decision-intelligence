# Roadmap

Only items that are still actually missing.

## Near-term (code-shaped, not claimed done)

1. Recapture Streamlit screenshots after UI changes (`screenshots/nexus/`).
2. True time-based churn labels (hide last N days of orders, predict next window).
3. Chunking experiments with measured recall on a larger policy corpus.
4. Optional NetworkX/Neo4j live rebuild job that **replaces** the committed 41/112 snapshot after a measured run.

## Shipped in 1.5

- Inferential engineering (`inferential/`): estimand, identification, stratified risk difference, nullification bias, and an action verdict.
- `warehouse_late_gap` can rank a warehouse. `advance_selection` is computed and then marked `do_not_claim`.
- Board endpoint, Streamlit **Inferential** tab, and a one-line claim on investigate plus the Monday brief.
- LLM inference gateway is unchanged and is a different subsystem.
- Agent action cards and ledger proposals carry the extract window (2015-01-01 → 2018-01-31) and the metric definition, so a late-line dollar cannot be read as lost sales. The AI Analyst shows the action first and labels confidence as evidence completeness.

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
