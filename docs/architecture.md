# NEXUS architecture

Local-first **enterprise decision intelligence** for retail and supply-chain operations. One warehouse, one investigate API, one Streamlit console. Version **1.4**.

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
    Q[Quality command: freshness / drift / nulls / dupes]
  end
  subgraph consume [Consumers]
    KPI[Metric views + dictionary]
    PBI[Power BI .pbip]
    DS[Hypothesis / RCA / A/B calculator]
    ML[Forecast / anomaly / churn / stockout]
    RAG[Hybrid RAG over SAMPLE SOPs]
    G[GraphRAG 41/112 snapshot]
    TWIN[Linear SAMPLE twin]
    AG[Investigate graph]
    COP[Monday brief MD/PDF]
  end
  subgraph inf [Inference gateway]
    GR[Guardrails]
    QU[Queue + retry]
    R[Router small/med/large]
    M[Mock default]
    H[OpenAI-compatible HTTP]
  end
  subgraph plat [Platform]
    API[FastAPI]
    UI[Streamlit]
    MEM[JSON memory]
    STR[In-process week replay]
    PROM[/metrics Prometheus text]
  end
  DC --> L
  UK --> L --> C --> W
  C --> Q
  W --> KPI --> PBI
  W --> DS
  W --> ML
  W --> G
  W --> TWIN
  W --> AG
  RAG --> AG
  G --> AG
  ML --> AG
  AG --> COP
  AG --> API
  GR --> QU --> R
  R --> M
  R --> H
  H --> API
  M --> API
  API --> UI
  API --> PROM
  STR --> UI
  MEM --> UI
```

## Runtime defaults

| Concern | Default | Optional |
|---|---|---|
| Warehouse | DuckDB file | None in-repo |
| Graph | Snapshot JSON + dict graph | NetworkX extra; Neo4j if `NEO4J_URI` |
| Twin | Linear SAMPLE elasticities | None — not a physics twin |
| LLM | Mock templates | `OPENAI_*`, `GROQ_*`, `OLLAMA_BASE_URL`, `VLLM_BASE_URL`, `LLAMACPP_BASE_URL` |
| Embeddings | Hashing vectors | `sentence-transformers` + FAISS |
| Agents | Local linear graph + retries | LangGraph if installed |
| Streaming | In-process week replay | Kafka if `KAFKA_BOOTSTRAP` |
| Memory | `artifacts/memory.json` | None hosted |
| Tracking | JSON files under `ml/tracking` | MLflow if installed |
| Auth | `X-API-Key` (constant-time compare) | `X-Nexus-Role`: viewer / analyst / admin |
| Metrics | Prometheus text on `/metrics` | Import Grafana JSON yourself |

## Investigate path

1. Guardrails scan injection / jailbreak / PII.
2. Orchestrator records plan (`langgraph` or `local_graph`).
3. Analytics/SQL agent runs curated SELECT snippets (write keywords refused).
4. Forecast agent reads `ml/registry`.
5. Inventory and risk agents query metric views.
6. RAG + GraphRAG return cited chunks / paths.
7. Decision agent emits recommendations (held if `human_review=true`).
8. Confidence is an **evidence completeness score**, not model accuracy.

## What is not in process

No vLLM/Ollama/Grafana/MLflow/Neo4j/Kafka **servers** are started by `docker compose`. Adapters exist so you can wire them without inventing a fleet.
