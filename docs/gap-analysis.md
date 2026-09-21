# Gap analysis

Compared to a real enterprise decision-intelligence platform. Updated for v1.4 (GraphRAG, linear twin, eval, inference queue, quality command, guardrails, memory, replay).

| Capability | This repo | Typical enterprise | Gap |
|---|---|---|---|
| Ingestion | Batch parquet copy | CDC, streaming, SLA pages | Large |
| Warehouse | Single DuckDB file | Cloud warehouse + governance | Large |
| Contracts | YAML + SQL checks | Great Expectations / Unity Catalog | Medium |
| Quality | Extract snapshot score (11 checks) | Always-on monitors + paging | Medium |
| BI | Power BI pbip + Streamlit | Certified semantic models + RLS at scale | Medium (RLS exists in pbip) |
| Science | Offline modules | Experimentation platform | Medium |
| ML | sklearn + optional boosters | Feature store, scheduled retrain | Medium |
| RAG | 5 SAMPLE docs | Curated corpus, ACL, eval judges | Large on corpus |
| GraphRAG | 41/112 snapshot, Neo4j idle | Live knowledge graph + ACL | Large until you run Neo4j |
| Twin | Linear SAMPLE elasticities | Network digital twin | Large (honest) |
| Agents | In-process graph + gold eval | Durable workflows, HITL queues | Medium |
| Inference | Mock + HTTP adapters + queue/retry | Autoscaled engines, canary | Large until you run an engine |
| Streaming | Week replay; Kafka adapter idle | OMS CDC | Large |
| Memory | JSON file | Case management | Large |
| AuthN/Z | Shared key + role header | SSO, ABAC | Large |
| Secrets | `.env` | Vault / cloud SM | Large |
| HA | None | Multi-AZ | Total |
| PII | Names in extract; GraphRAG uses segments | Redaction, DLP | High risk if published as a demo with real names |

Closing the “adapter” gaps is documented; closing the “run a fleet” gaps is out of scope for a portfolio clone.
