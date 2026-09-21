# Design decisions

| Decision | Choice | Why |
|---|---|---|
| One business problem | Retail + supply-chain decision intelligence | Avoid a junk drawer of unrelated demos |
| Warehouse | DuckDB on parquet | Zero-ops, CI-friendly, matches analyst SQL |
| Contracts | YAML + DuckDB checks | Readable in PRs; no extra pandera dependency |
| Incremental load | SHA256 skip | Full reload still available (`incremental=False`) |
| KPI semantics | `analytics/metrics/dictionary.yaml` | Executives need definitions, not only charts |
| Forecast registry | sklearn HistGradientBoosting | Always installable; XGBoost/LightGBM compared only if present |
| Churn label | 180-day inactivity proxy | Documented leakage; registry drops recency |
| Stockout model | Median stockout-rate split | Explicitly a ranking demo, not a causal risk engine |
| RAG | Hybrid lexical + dense | Dense uses hashing fallback without downloads |
| pgvector | SQL file only | Default store is DuckDB; Postgres is optional ops |
| Agents | LangGraph if importable else local graph | Demo works offline; no fake Cloud graphs |
| Inference | Mock default + OpenAI-compatible HTTP | No GPU claims; live path is env-gated |
| Batching | Sequential `complete_batch` | Continuous batching needs a real engine (vLLM) |
| Observability | Prometheus text + Grafana JSON | We do not ship a Grafana container as “production monitoring” |
| Auth | Shared API key + role header | Portfolio hardening, not SSO |
| Power BI | Keep `.pbip` | Existing BI asset mapped into Command Center |

## Evidence rules

- Confidence on `/investigate` counts SQL hits, docs, and registry files.
- RAG eval reports recall/precision vs gold doc ids. Faithfulness is `null` until a judge exists.
- Inference `tokens_per_sec` on mock is sleep-based, not hardware throughput.
