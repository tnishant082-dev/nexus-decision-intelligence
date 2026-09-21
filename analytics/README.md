# NEXUS Analytics Layer

SQL KPI queries live in `analytics/sql/` (copied/extended from the original control-tower SQL).
The Power BI project under `dashboard/SupplyChain-Control-Tower.pbip` remains the **BI Analytics** surface.

## Power BI → NEXUS Executive Command Center map

| Power BI page (screenshots/) | NEXUS role |
|---|---|
| Executive Command Center | Command Center — finance + working capital |
| Supply Chain Control Tower / sc-tower | Service control — OTIF, fill, perfect order |
| Logistics Intelligence | Carrier / mode / delay / freight |
| Inventory Command Center | Coverage, turns, ABC |
| Warehouse Analytics / Warehouse 360 | Node throughput & utilization |
| Procurement Intelligence | PO spend, cycle, preferred mix |
| Vendor Performance Hub | Reliability, SLA, risk |
| Order Fulfillment / Order Detail | Perfect order & status drill |
| Customer 360 | Revenue, returns, OTIF by customer |
| Sustainability Dashboard | CO2, mode mix |

Streamlit **Analytics** tab runs warehouse views (`v_exec_kpis`, `v_otif_order`, `v_fill_rate`, `v_logistics`, `v_inventory_kpis`, `v_customer_kpis`, `v_demand_weekly`) for local investigation without Power BI Desktop.

Metric definitions: [`metrics/dictionary.yaml`](./metrics/dictionary.yaml).
