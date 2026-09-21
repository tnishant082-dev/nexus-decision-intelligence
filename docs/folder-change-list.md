# Folder-by-folder change list

| Path | Change |
|---|---|
| `data-engineering/contracts/` | New YAML contracts + loader |
| `data-engineering/etl/land.py` | Incremental copy via SHA256 |
| `data-engineering/etl/warehouse.py` | Incremental table load + extra KPI views |
| `data-engineering/validation/` | Contract validator; stronger checks |
| `data-engineering/quality/` | Profile + freshness reports |
| `data-engineering/catalog/` | JSON + markdown catalog |
| `data-engineering/lineage/` | JSON + mermaid |
| `data-engineering/run_pipeline.py` | Orchestrates quality artifacts |
| `analytics/metrics/` | Metric dictionary |
| `analytics/sql/05_metric_views.sql` | Analyst copies of views |
| `data-science/modules/` | CI helpers, RCA, correlation, A/B, richer EDA |
| `ml/estimators.py` | Optional XGBoost/LightGBM |
| `ml/explain.py` | Importances + optional SHAP |
| `ml/tracking.py` | File runs + optional MLflow |
| `ml/drift.py` | PSI |
| `ml/train_forecast.py` | Comparison vs lag-1 |
| `ml/train_stockout.py` | New proxy classifier |
| `ml/serving/predict.py` | Stockout serving |
| `ml/run_all.py` / `retrain.py` | Combined train + drift |
| `ai/rag/` | Hybrid, embeddings, eval, pgvector.sql |
| `ai/agents/` | Graph, nodes, human review |
| `ai/tools/sql_tool.py` | Extra snippets |
| `inference/` | HTTP providers, TTFT/cost, batch |
| `backend/` | CORS, roles, audit, metrics, extra routes |
| `frontend/streamlit_app.py` | Charts, exports, richer KPIs |
| `observability/` | Prometheus + Grafana JSON |
| `tests/` | Metrics, RAG, agents, API extras |
| `docs/` | Audit, architecture, deployment, roadmap, gap, resume pack |
| `README.md` | Recruiter rewrite |
| `requirements-optional.txt` | Heavy extras not in CI |
| `.env.example` | Provider env vars |

Unchanged in spirit: `dashboard/` Power BI project, `data/` extracts, SAMPLE policies.
