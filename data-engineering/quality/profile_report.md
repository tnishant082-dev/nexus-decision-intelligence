# Warehouse profile

Generated `2026-09-21T22:01:27.475528+00:00`

## fact_orders (180519 rows)

| column | dtype | nulls | distinct |
|---|---|---|---|
| `order_line_key` | BIGINT | 0 | 180519 |
| `order_item_id` | INTEGER | 0 | 180519 |
| `order_id` | INTEGER | 0 | 65752 |
| `order_date_key` | INTEGER | 0 | 1127 |
| `order_ts` | TIMESTAMP | 0 | 65752 |
| `customer_key` | INTEGER | 0 | 20652 |
| `product_key` | INTEGER | 0 | 118 |
| `region_key` | INTEGER | 0 | 3772 |
| `warehouse_key` | INTEGER | 0 | 5 |
| `vendor_key` | INTEGER | 0 | 11 |
| `transport_mode_key` | INTEGER | 0 | 4 |
| `carrier_key` | INTEGER | 0 | 4 |
| `order_status_key` | INTEGER | 0 | 9 |
| `payment_type_key` | INTEGER | 0 | 4 |
| `source_system_key` | INTEGER | 0 | 1 |
| `quantity` | INTEGER | 0 | 5 |
| `unit_price` | DOUBLE | 0 | 75 |
| `gross_sales` | DOUBLE | 0 | 193 |
| `discount_amount` | DOUBLE | 0 | 1017 |
| `discount_rate` | DOUBLE | 0 | 18 |
| `net_sales` | DOUBLE | 0 | 2927 |
| `line_profit` | DOUBLE | 0 | 21998 |
| `profit_ratio` | DOUBLE | 0 | 162 |
| `cogs_amount` | DOUBLE | 0 | 59317 |
| `days_ship_real` | SMALLINT | 0 | 7 |
| `is_canceled` | BIGINT | 0 | 2 |
| `is_fraud` | BIGINT | 0 | 2 |
| `is_revenue` | BIGINT | 0 | 2 |
| `is_late` | BIGINT | 0 | 2 |
| `is_on_time` | BIGINT | 0 | 2 |
| `is_otif` | BIGINT | 0 | 2 |
| `is_perfect_order` | BIGINT | 0 | 2 |

## fact_shipments (65752 rows)

| column | dtype | nulls | distinct |
|---|---|---|---|
| `shipment_key` | BIGINT | 0 | 65752 |
| `order_id` | INTEGER | 0 | 65752 |
| `order_date_key` | INTEGER | 0 | 1127 |
| `ship_date_key` | INTEGER | 0 | 1131 |
| `order_ts` | TIMESTAMP | 0 | 65752 |
| `ship_ts` | TIMESTAMP | 0 | 63701 |
| `customer_key` | INTEGER | 0 | 20652 |
| `region_key` | INTEGER | 0 | 3772 |
| `warehouse_key` | INTEGER | 0 | 5 |
| `transport_mode_key` | INTEGER | 0 | 4 |
| `carrier_key` | INTEGER | 0 | 4 |
| `delivery_status_key` | INTEGER | 0 | 4 |
| `order_status_key` | INTEGER | 0 | 9 |
| `source_system_key` | INTEGER | 0 | 1 |
| `days_ship_real` | SMALLINT | 0 | 7 |
| `days_ship_scheduled` | SMALLINT | 0 | 4 |
| `days_delay` | SMALLINT | 0 | 7 |
| `late_delivery_risk` | BOOLEAN | 0 | 2 |
| `is_late` | BIGINT | 0 | 2 |
| `is_on_time` | BIGINT | 0 | 2 |
| `is_advance` | BIGINT | 0 | 2 |
| `is_canceled_ship` | BIGINT | 0 | 2 |
| `is_in_full` | BIGINT | 0 | 2 |
| `is_otif` | BIGINT | 0 | 2 |
| `is_perfect_order` | BIGINT | 0 | 2 |
| `line_count` | BIGINT | 0 | 5 |
| `unit_count` | INTEGER | 0 | 24 |
| `net_sales_amount` | DOUBLE | 0 | 44123 |
| `freight_cost` | DOUBLE | 0 | 92 |
| `delay_cost` | DOUBLE | 0 | 9 |
| `co2_kg` | DOUBLE | 0 | 116 |
| `distance_km_proxy` | DOUBLE | 0 | 6 |

## fact_inventory (245072 rows)

| column | dtype | nulls | distinct |
|---|---|---|---|
| `inventory_key` | BIGINT | 0 | 245072 |
| `date_key` | INTEGER | 0 | 1133 |
| `product_key` | INTEGER | 0 | 118 |
| `warehouse_key` | INTEGER | 0 | 5 |
| `vendor_key` | INTEGER | 0 | 11 |
| `source_system_key` | INTEGER | 0 | 1 |
| `on_hand_units` | DOUBLE | 0 | 2533 |
| `on_hand_value` | DOUBLE | 0 | 5457 |
| `receipts_units` | DOUBLE | 0 | 468 |
| `issues_units` | DOUBLE | 0 | 118 |
| `demand_units` | DOUBLE | 0 | 118 |
| `unfilled_units` | DOUBLE | 0 | 14 |
| `unfilled_value` | DOUBLE | 0 | 48 |
| `backorder_units` | DOUBLE | 0 | 19 |
| `backorder_value` | DOUBLE | 0 | 58 |
| `stockout_flag` | BIGINT | 0 | 2 |
| `safety_stock_units` | DOUBLE | 0 | 375 |
| `reorder_point_units` | DOUBLE | 0 | 375 |
| `target_dos` | DOUBLE | 0 | 1 |
| `snapshot_ts` | TIMESTAMP | 0 | 1133 |
| `source_class` | VARCHAR | 0 | 1 |

## dim_customer (20653 rows)

| column | dtype | nulls | distinct |
|---|---|---|---|
| `customer_key` | BIGINT | 0 | 20653 |
| `customer_id_src` | DOUBLE | 1 | 20652 |
| `customer_name` | VARCHAR | 0 | 14034 |
| `first_name` | VARCHAR | 1 | 782 |
| `last_name` | VARCHAR | 1 | 1110 |
| `segment` | VARCHAR | 0 | 4 |
| `bill_to_city` | VARCHAR | 1 | 563 |
| `bill_to_state` | VARCHAR | 1 | 46 |
| `bill_to_postal` | VARCHAR | 4 | 995 |
| `bill_to_country` | VARCHAR | 0 | 3 |
| `bill_to_country_iso` | VARCHAR | 1 | 2 |
| `latitude` | DOUBLE | 1 | 11250 |
| `longitude` | DOUBLE | 1 | 4487 |
| `first_order_date` | DATE | 1 | 1024 |
| `last_order_date` | DATE | 1 | 1012 |
| `lifetime_orders` | BIGINT | 0 | 16 |
| `source_system_key` | BIGINT | 0 | 2 |

## dim_product (119 rows)

| column | dtype | nulls | distinct |
|---|---|---|---|
| `product_key` | BIGINT | 0 | 119 |
| `product_id_src` | DOUBLE | 1 | 118 |
| `product_nk` | VARCHAR | 0 | 119 |
| `product_name` | VARCHAR | 0 | 119 |
| `category_id` | DOUBLE | 1 | 51 |
| `category_name` | VARCHAR | 0 | 51 |
| `category_group` | VARCHAR | 0 | 51 |
| `department_id` | DOUBLE | 1 | 11 |
| `department_name` | VARCHAR | 0 | 12 |
| `vendor_key` | BIGINT | 0 | 12 |
| `list_price` | DOUBLE | 0 | 76 |
| `abc_class` | VARCHAR | 0 | 3 |
| `is_active` | BIGINT | 0 | 2 |
| `source_system_key` | BIGINT | 0 | 2 |
