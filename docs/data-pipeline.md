# Data pipeline

```
DataCo parquet + Online Retail II parquet
  → land (SHA256 manifest)
  → clean + YAML contracts
  → DuckDB nexus.duckdb
  → KPI views / ML / GraphRAG snapshot / quality snapshot
```

Window: **2015-01-01 → 2018-01-31**. Historical public extracts.

Quality command (`quality/command.py`) scores the extract snapshot:

- Freshness vs extract end (lag vs today is informational, not an incident)
- Schema drift vs the 32-column `fact_orders` contract
- Null monitoring on keys / net_sales / is_otif / is_late
- Duplicate `order_line_key`
- Open incidents list (empty on this snapshot)

Score 100 = 11/11 checks on the committed snapshot. Re-run `python data-engineering/run_pipeline.py` rather than treating the number as a live SLA.
