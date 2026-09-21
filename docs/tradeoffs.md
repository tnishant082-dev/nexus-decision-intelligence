# Tradeoffs

| Choice | Gain | Cost |
|---|---|---|
| DuckDB file | Fast local analytics | Not multi-writer, not an enterprise warehouse |
| Mock LLM default | Offline CI and honest demos | No free-form reasoning until a provider is configured |
| Hashing embeddings | No model download | Weaker semantic recall than MiniLM |
| sklearn serving | Thin Docker image | Not the same artifact as an XGBoost experiment |
| Keyword SQL guard | Blocks casual DML | Not a parser sandbox |
| Heuristic prompt guards | Cheap injection/PII/SQL write blocks | Easy to evade; not a model firewall |
| Graph snapshot JSON | Reproducible GraphRAG without Neo4j | Stale until you rebuild from parquet |
| Linear SAMPLE twin | Runnable what-ifs on real KPIs | Not OMS/WMS physics |
| In-memory rate limit | Simple | Not distributed |
| Snapshot inventory KPIs | Uses real tables | Turns/coverage are proxies, not finance-grade |
| Sequential agent graph | Debuggable trail | Not a durable workflow engine |
| Week replay vs Kafka | Works offline | Not live orders |
| JSON memory | Past-incident questions demo | Not a case-management system |
| Grafana JSON in git | Shows metric names | Dashboard is unused until you run Grafana |
| Keep Power BI + Streamlit | Two audiences | Two UIs to maintain |

See also `docs/design-decisions.md`, `docs/data-scope.md`, `docs/limitations.md`.
