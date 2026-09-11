# NEXUS Architecture

```mermaid
flowchart TB
  subgraph Sources
    DC[DataCo extract]
    OR[Online Retail II extract]
  end
  subgraph DE[Data Engineering]
    L[Landing parquet]
    C[Cleaned]
    W[(DuckDB warehouse)]
  end
  subgraph Analytics
    SQL[KPI SQL / views]
    PBI[Power BI .pbip]
  end
  subgraph DS[Data Science]
    EDA[EDA + hypothesis]
    SEG[Segmentation]
  end
  subgraph ML
    F[Demand forecast]
    A[OTIF anomaly]
    CH[Churn proxy]
    REG[Model registry]
  end
  subgraph AI
    RAG[RAG over sample SOPs]
    AG[Investigate multi-agent]
  end
  subgraph Inference
    GW[Gateway + router]
    CACHE[Response cache]
  end
  subgraph Platform
    API[FastAPI]
    UI[Streamlit console]
  end
  DC --> L
  OR --> L
  L --> C --> W
  W --> SQL
  C --> PBI
  W --> EDA
  W --> SEG
  W --> F --> REG
  W --> A --> REG
  W --> CH --> REG
  W --> AG
  RAG --> AG
  REG --> AG
  AG --> API
  GW --> API
  CACHE --> GW
  API --> UI
```

## Local-first defaults
- LLM: **mock** templates via inference router (`mock` / `small` / `large` labels)
- Warehouse: DuckDB file under `data-engineering/warehouse/nexus.duckdb`
- Auth: shared API key header (`X-API-Key`)
