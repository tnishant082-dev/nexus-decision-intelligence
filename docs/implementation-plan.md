# Implementation plan (executed on branch `platform-enterprise-upgrade`)

Work stayed inside **one** product: executive questions on revenue, OTIF, stockouts, churn, and next actions.

| Step | Intent | What shipped in code | What was not faked |
|---|---|---|---|
| 1 Audit | Baseline | `docs/repository-audit.md` | Scores are judgment, not a cert |
| 2 Data engineering | Contracts, DQ, incremental | YAML contracts, validation, profile, freshness, SHA skip loads, catalog.md, lineage.md | Not a commercial catalog |
| 3 Analytics | Exec KPIs | Views + `analytics/metrics/dictionary.yaml` + SQL tests | Turns/coverage are proxies |
| 4 Data science | Inference stats | Welch + CI + RCA + corr + A/B calculator | A/B is a calculator on counts you supply |
| 5 ML | Production-shaped training | Estimator comparison, SHAP if installed, stockout proxy, file tracking, PSI drift | No unpublished accuracy |
| 6 RAG | Hybrid + eval | Hash/ST embeddings, FAISS optional, citations, recall harness | Faithfulness = null |
| 7 Agents | Graph | LangGraph optional; local graph + retries + human_review | Not LangGraph Cloud |
| 8 Inference | Gateway | OpenAI-compatible HTTP adapters; mock default; TTFT/cost logs | No GPU, no running vLLM |
| 9 MLOps | Registry/retrain | JSON + optional MLflow; `ml/retrain.py` | No hosted registry |
| 10 Observability | Scrapable metrics | `/metrics` + Grafana JSON | Grafana not started |
| 11 Security | Demo hardening | hmac compare, CORS list, audit, roles | Not SSO |
| 12 Frontend | Console | Charts, export, human review | Screenshots not recaptured |
| 13–14 Docs | Recruiter README | This docs set | No fake benchmarks |

## Suggested PR slices

See `docs/pr-roadmap.md`.
