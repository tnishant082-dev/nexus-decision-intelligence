# Data Scope & Assumptions

## Sources (cited)
1. **DataCo Smart Supply Chain** — primary orders, shipments, inventory, logistics flags (`dim_source_system.source_code = DATACO`). Date dimension includes `is_partial_dataco_year`.
2. **Online Retail II (UK)** — customer/retail enrichment (`RETAIL_UK` in source system dim).
3. Tokenized web access logs appear as `WEB` for reference only.

## Window
Order activity in this extract spans **2015-01-01 → 2018-01-31**.

## What the KPIs mean
Figures in the README and Command Center are **computed from the included parquet / DuckDB warehouse**, not invented SaaS metrics.

Examples (recomputed by pipeline views):
- Revenue ≈ **$31.6M**, Profit ≈ **$3.8M**, Orders ≈ **63K**
- OTIF (order grain) ≈ **40.8%**, Perfect order ≈ **18.8%**
- Shipment delay rate ≈ **54.8%**, Freight ≈ **$1.0M**, CO2 ≈ **386.6 t**

## Assumptions
- OTIF / late / perfect-order flags are as provided in the modeled extract.
- Inventory “on hand $” across all snapshots is not a single-day balance sheet — use carefully.
- Policies in `docs/knowledge/` are **SAMPLE** documents for RAG demos.
- This is a **local portfolio platform**, not a hosted production control tower.
