# Resume bullets, portfolio blurb, GitHub topics

Use only after you can run the commands yourself. Do **not** add accuracy, GPU, or “production at company X” language.

## Resume bullets (verified capabilities)

- Built a local-first **retail/supply-chain decision intelligence** platform (DuckDB, FastAPI, Streamlit) that answers executive questions on revenue, OTIF, inventory, and churn with SQL evidence.
- Implemented **data contracts**, incremental parquet loads, freshness/profile reports, and a metric dictionary with SQL tests for finance, ops, inventory, and customer KPIs.
- Trained leakage-aware **churn**, category-week **forecast vs lag-1 naive**, IsolationForest **OTIF anomalies**, and a documented **stockout-risk proxy**; logged runs to a file registry (MLflow optional).
- Shipped **hybrid RAG** (lexical + dense, citations) and a **multi-agent investigate graph** (LangGraph if installed) with retries and a human-review flag.
- Designed an **inference gateway** with mock default and OpenAI-compatible adapters (OpenAI/Groq/Ollama/vLLM/llama.cpp HTTP), plus Prometheus-format `/metrics` (TTFT, tokens, cache, cost fields).

## Portfolio short description

NEXUS is a single-domain decision-intelligence demo: public DataCo + Online Retail II extracts land in DuckDB; executives query KPIs or `/api/v1/investigate` and get drivers, SAMPLE-policy citations, and model-registry ids. LLMs default to mock so the repo stays honest offline.

## GitHub topics

`data-engineering` `duckdb` `analytics` `supply-chain` `otif` `machine-learning` `rag` `agents` `fastapi` `streamlit` `mlops` `inference` `portfolio`

## Interview talking points

- Why OTIF is ~40% in this extract (flags, not a broken KPI formula).
- Why churn AUC with recency is leaky.
- Why inventory on-hand $ summed over snapshots is not a balance sheet.
- What happens if Groq is down (mock fallback).
