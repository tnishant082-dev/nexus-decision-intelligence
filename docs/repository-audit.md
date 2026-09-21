# Repository audit — NEXUS Decision Intelligence

**Audited:** 21 September 2026  
**Revision:** GitHub `tnishant082-dev/nexus-decision-intelligence` at `b680560` (pre-upgrade baseline), plus this branch’s changes.  
**Scope:** Local-first portfolio platform for retail and supply-chain decision intelligence. Not a hosted multi-tenant product.

Scores below are **engineering judgments from inspected code**, not marketing grades. Nothing here claims live GPU throughput, SaaS SLAs, or unpublished model accuracy.

---

## Executive snapshot

| Dimension | Baseline (pre-upgrade) | After this branch (code-backed) |
|---|---|---|
| Coherence around one business problem | Strong | Strong |
| Data engineering | Landing + clean + DuckDB + light checks | Contracts, incremental load, profiling, freshness, catalog/lineage artifacts |
| Analytics | Exec/OTIF/logistics views + Power BI | Metric dictionary + additional KPI views + SQL tests |
| Data science | One Welch t-test + ABC slice | Hypothesis, CIs, RCA, correlation, A/B harness, documented limitations |
| Machine learning | sklearn forecast / IsolationForest / churn proxy | Multi-estimator comparison with sklearn fallback; leakage-aware churn; stockout risk; file registry |
| RAG | Lexical overlap | Hybrid lexical + optional dense/FAISS; citations; offline eval harness |
| Agents | Sequential named steps, mock synthesis | Graph orchestration (LangGraph if installed, local graph otherwise), retries, human-review flag |
| Inference | Sleep + template mock | Gateway with OpenAI/Groq/Ollama/llama.cpp/vLLM-compatible HTTP **when configured**; mock default |
| MLOps | JSON registry + experiment files | File tracking store, versions, drift job, retrain entrypoint |
| Observability | Partial Prometheus text + SQLite logs | Expanded `/metrics`, Grafana JSON, optional OpenTelemetry no-op |
| Security | Shared API key, in-memory rate limit, SELECT guard | Constant-time key compare, CORS allow-list, audit log, role header |
| Frontend | Streamlit tabs matching README | Same tabs with charts, exports, human-review toggle |
| Testing | Pipeline + API pytest | Broader unit tests; CI still mock/offline |

**Baseline production-readiness (hosted enterprise):** **4.0 / 10**  
**This branch, still local-first:** **6.2 / 10**  

Neither score means “ready to run a global retailer’s production control tower.” Both mean “portfolio system with honest defaults.”

---

## Strengths (verified in source)

1. **Single domain.** DataCo + Online Retail II extracts feed one warehouse, KPI views, models, RAG policies, and `/api/v1/investigate`.
2. **Honesty culture.** README and `docs/data-scope.md` refuse invented accuracy and GPU claims. Churn registry uses the **without-recency** model and labels the recency AUC as leaky.
3. **Runnable offline path.** DuckDB, FastAPI, Streamlit, mock LLM, pytest session warehouse bootstrap.
4. **Read-only SQL tool.** Keyword block on DML/DDL; queries must start with `SELECT`/`WITH`.
5. **Existing BI asset.** Power BI `.pbip` is retained as the analytics layer, mapped in `analytics/README.md`.
6. **CI.** GitHub Actions installs requirements, builds warehouse, runs pytest.

---

## Weaknesses (baseline)

1. **Mock-first inference** slept a few milliseconds and returned a hash-tagged template. Router labels `small`/`large` were slots, not models.
2. **Agents were sequential functions**, not a durable graph with retries, interrupts, or tool schemas.
3. **RAG was token overlap** over five SAMPLE markdown files. No embeddings, no hybrid, no faithfulness metrics in CI.
4. **Warehouse rebuild was full reload** (`unlink` DuckDB every run). No contracts, weak “revenue_nonneg” check (`lambda n: True`).
5. **ML stack was sklearn-only.** No estimator comparison artifacts, no SHAP unless added later, no stockout classifier.
6. **Auth was equality on a default key** `dev-nexus-key`. CORS `allow_origins=["*"]`. No audit trail.
7. **Metrics endpoint** only emitted inference counters; no agent/pipeline series.
8. **Docs were thin** (`architecture.md` ~60 lines). Recruiter README existed but under-specified setup failure modes.
9. **Tests** did not cover contracts, metric SQL, RAG eval, or provider adapters.
10. **No MLflow server, no Prometheus/Grafana runtime, no vLLM process** in compose — names in a README would have been overclaim.

---

## Missing enterprise components (still missing after this branch unless an operator adds them)

These are **not** implemented as running production services in this repository:

- Multi-region HA warehouse (Snowflake/BigQuery/Databricks)
- SSO / OIDC / SCIM
- Secret manager (Vault/AWS SM) — env vars only
- Distributed rate limiting / WAF
- Real-time CDC from OMS/WMS/TMS
- GPU cluster, vLLM/Ollama **daemons** (adapters only)
- Managed MLflow/Feast/Airflow
- PII redaction pipeline for `dim_customer` names
- Load-tested SLOs

The branch adds **code-shaped substitutes** (file registry, HTTP adapters, Grafana JSON, compose comments) so a recruiter can see the seams without fake “we run this in prod” language.

---

## Architecture (as implemented)

```
Public extracts (parquet)
  → land (hash manifest, incremental skip)
  → clean (flags, contracts)
  → DuckDB warehouse + metric views
       → SQL analytics / Power BI
       → DS modules (tests, RCA, segments)
       → ML train/compare/registry/drift
       → Investigate graph (SQL + RAG + models)
  → FastAPI (API key, roles, audit, /metrics)
  → Streamlit console
  → Inference gateway (mock default | HTTP providers)
```

---

## Security notes

- Default key is for **local demo only**.
- Customer names in the public extract are **demo PII**.
- SQL tool is best-effort keyword filtering, not a full parser sandbox.
- Do not expose Docker ports to the internet with the sample key.

---

## Testing & MLOps / inference maturity

| Area | Maturity |
|---|---|
| Unit/API tests | Medium — pytest covers health, auth, investigate, SQL guard, RAG, mock inference |
| Data tests | Medium after upgrade — contract + metric SQL tests |
| Experiment tracking | File JSON (+ optional MLflow if installed) |
| Model registry | File JSON with `stage` |
| Drift | PSI-style job on numeric features; not a live monitor |
| Inference | Adapter-grade; default mock; TTFT/tokens recorded when a provider returns usage |
| Tracing | In-process agent trail; OTel export only if SDK installed |

---

## Top improvements ranked by impact

| Rank | Improvement | Why it matters | Status on this branch |
|---|---|---|---|
| 1 | Honest inference adapters + gateway metrics | Stops mock-only architecture without faking GPUs | Implemented |
| 2 | Metric dictionary + SQL-tested KPIs | Executives can trust definitions | Implemented |
| 3 | Graph agents with evidence + human review | Matches “why / what next” product | Implemented |
| 4 | Hybrid RAG + cited eval harness | Policies become inspectable | Implemented (dense optional) |
| 5 | Data contracts + incremental + freshness | DE credibility | Implemented |
| 6 | Estimator comparison + leakage notes | ML credibility | Implemented |
| 7 | Auth/audit/CORS hardening | Stops trivial demo holes | Implemented (still demo-grade) |
| 8 | Observability artifacts | Shows how you would run it | Partial (no hosted Grafana) |
| 9 | Recapture UI screenshots | README images can lag UI | **Not done** — keep existing captures |
| 10 | Live model eval with a real LLM | Quality numbers | **Out of scope** unless keys + authorization |

---

## Production-readiness scorecard (this branch)

| Criterion | Score / 10 | Comment |
|---|---|---|
| Correctness of local analytics path | 8 | Warehouse views + tests |
| Reproducibility | 8 | Scripts + CI |
| Security | 5 | API key demo, not SSO |
| Scalability | 4 | Single DuckDB file |
| HA / DR | 2 | None |
| Observability | 6 | Prometheus text + logs; Grafana JSON unused until you run Grafana |
| ML governance | 6 | File registry, drift job |
| Inference production | 5 | HTTP adapters; no fleet |
| Documentation honesty | 9 | Explicit limitations |
| **Weighted overall** | **6.2** | Local flagship portfolio |

---

## What recruiters should not hear

- “Production OTIF model at 91% accuracy”
- “We serve vLLM on GPUs in this repo”
- “LangGraph Cloud / enterprise RAG platform”
- “Real-time supply chain twin”

Say instead: local DuckDB decision-intelligence system, mock-default LLM, optional OpenAI-compatible providers, evidence-backed investigate API, public extracts.
