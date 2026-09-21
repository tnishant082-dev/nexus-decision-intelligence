# Gap analysis

Compared to a real enterprise decision-intelligence platform.

| Capability | This repo | Typical enterprise | Gap |
|---|---|---|---|
| Ingestion | Batch parquet copy | CDC, streaming, SLA pages | Large |
| Warehouse | Single DuckDB file | Cloud warehouse + governance | Large |
| Contracts | YAML + SQL checks | Great Expectations / Unity Catalog | Medium |
| BI | Power BI pbip + Streamlit | Certified semantic models + RLS at scale | Medium (RLS exists in pbip) |
| Science | Offline modules | Experimentation platform | Medium |
| ML | sklearn + optional boosters | Feature store, scheduled retrain | Medium |
| RAG | 5 SAMPLE docs | Curated corpus, ACL, eval judges | Large on corpus |
| Agents | In-process graph | Durable workflows, HITL queues | Medium |
| Inference | Mock + HTTP adapters | Autoscaled engines, canary | Large until you run an engine |
| AuthN/Z | Shared key + role header | SSO, ABAC | Large |
| Secrets | `.env` | Vault / cloud SM | Large |
| HA | None | Multi-AZ | Total |
| PII | Names in extract | Redaction, DLP | High risk if published as a demo with real names |

Closing the “adapter” gaps is documented; closing the “run a fleet” gaps is out of scope for a portfolio clone.
