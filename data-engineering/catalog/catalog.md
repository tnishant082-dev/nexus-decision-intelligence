# NEXUS data catalog

Generated `2026-09-21T18:07:58.873329+00:00` from DuckDB.

## Tables

| table | rows | grain | domain | PII |
|---|---:|---|---|---|
| `dim_carrier` | 5 | unknown | other | False |
| `dim_customer` | 20653 | customer | crm | True |
| `dim_date` | 3318 | day | calendar | False |
| `dim_delivery_status` | 5 | unknown | other | False |
| `dim_order_status` | 10 | unknown | other | False |
| `dim_payment_type` | 5 | unknown | other | False |
| `dim_product` | 119 | product | mdm | False |
| `dim_region` | 3773 | unknown | other | False |
| `dim_source_system` | 4 | unknown | other | False |
| `dim_transport_mode` | 5 | unknown | other | False |
| `dim_vendor` | 13 | vendor | procurement | False |
| `dim_warehouse` | 7 | warehouse | wms | False |
| `fact_inventory` | 245072 | product x warehouse x date | wms | False |
| `fact_orders` | 180519 | order line | oms | False |
| `fact_procurement` | 8340 | PO line | procurement | False |
| `fact_returns` | 30644 | return line | oms | False |
| `fact_shipments` | 65752 | shipment | tms | False |
| `fact_vendor_performance` | 227 | unknown | other | False |
| `last_refresh` | 1 | unknown | other | False |
| `ref_emission_factor` | 4 | unknown | other | False |
| `ref_freight_tariff` | 4 | unknown | other | False |
| `ref_lane_distance` | 5 | unknown | other | False |
| `rls_user_map` | 9 | unknown | other | False |

## Views

| view | rows (scan) |
|---|---:|
| `v_customer_kpis` | 1 |
| `v_customer_ltv` | 20652 |
| `v_demand_weekly` | 4544 |
| `v_exec_kpis` | 1 |
| `v_fill_rate` | 1 |
| `v_finance_growth` | 4 |
| `v_inventory_kpis` | 1 |
| `v_inventory_latest` | 1 |
| `v_logistics` | 1 |
| `v_otif_order` | 1 |
| `v_stockout_risk` | 118 |
