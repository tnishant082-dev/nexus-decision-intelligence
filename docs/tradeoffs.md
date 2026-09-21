# Tradeoffs

| Choice | Gain | Cost |
|---|---|---|
| DuckDB file | Fast local analytics | Not multi-writer, not an enterprise warehouse |
| Mock LLM default | Offline CI and honest demos | No free-form reasoning until a provider is configured |
| Hashing embeddings | No model download | Weaker semantic recall than MiniLM |
| sklearn serving | Thin Docker image | Not the same artifact as an XGBoost experiment |
| Keyword SQL guard | Blocks casual DML | Not a parser sandbox |
| In-memory rate limit | Simple | Not distributed |
| Snapshot inventory KPIs | Uses real tables | Turns/coverage are proxies, not finance-grade |
| Sequential agent graph | Debuggable trail | Not a durable workflow engine |
| Grafana JSON in git | Shows metric names | Dashboard is unused until you run Grafana |
| Keep Power BI + Streamlit | Two audiences | Two UIs to maintain |

See also `docs/design-decisions.md` and `docs/data-scope.md`.
