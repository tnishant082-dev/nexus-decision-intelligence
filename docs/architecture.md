# NEXUS architecture

Local-first **enterprise decision intelligence** for retail and supply-chain operations. One warehouse, one investigate API, one Streamlit console.

```mermaid
flowchart TB
  subgraph sources [Public extracts]
    DC[DataCo Smart Supply Chain]
    UK[Online Retail II]
  end
  subgraph de [Data engineering]
    L[Landing + SHA256 manifest]
    C[Clean + YAML contracts]
    W[(DuckDB nexus.duckdb)]
    Q[Profile / freshness / validation]
  end
  subgraph consume [Consumers]
    KPI[Metric views + dictionary]
    PBI[Power BI .pbip]
    DS[Hypothesis / RCA / A/B calculator]
    ML[Forecast / anomaly / churn / stockout]
    RAG[Hybrid RAG over SAMPLE SOPs]
    AG[Investigate graph]
  end
  subgraph inf [Inference gateway]
    R[Router]
    M[Mock default]
    H[OpenAI-compatible HTTP]
  end
  subgraph plat [Platform]
    API[FastAPI]
    UI[Streamlit]
    PROM[/metrics Prometheus text]
  end
  DC --> L
  UK --> L --> C --> W
  C --> Q
  W --> KPI --> PBI
  W --> DS
  W --> ML
  W --> AG
  RAG --> AG
  ML --> AG
  AG --> API
  R --> M
  R --> H
  H --> API
  M --> API
  API --> UI
  API --> PROM
```

## Runtime defaults

| Concern | Default | Optional |
|---|---|---|
| Warehouse | DuckDB file | None in-repo |
| LLM | Mock templates | `OPENAI_*`, `GROQ_*`, `OLLAMA_BASE_URL`, `VLLM_BASE_URL`, `LLAMACPP_BASE_URL` |
| Embeddings | Hashing vectors | `sentence-transformers` + FAISS |
| Agents | Local linear graph + retries | LangGraph if installed |
| Tracking | JSON files under `ml/tracking` | MLflow if installed |
| Auth | `X-API-Key` (constant-time compare) | `X-Nexus-Role`: viewer / analyst / admin |
| Metrics | Prometheus text on `/metrics` | Import Grafana JSON yourself |

## Investigate path

1. Orchestrator records plan (`langgraph` or `local_graph`).
2. Analytics/SQL agent runs curated SELECT snippets.
3. Forecast agent reads `ml/registry`.
4. Inventory and risk agents query metric views.
5. RAG agent returns cited chunks.
6. Decision agent emits recommendations (held if `human_review=true`).
7. Confidence is an **evidence completeness score**, not model accuracy.

## What is not in process

No vLLM/Ollama/Grafana/MLflow **servers** are started by `docker compose`. Adapters and dashboard JSON exist so you can wire them without inventing a fleet.
