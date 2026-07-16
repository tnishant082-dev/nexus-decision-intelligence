-- executive finance snapshot
SELECT
    ROUND(SUM(net_sales) / 1000000, 1) AS revenue_m,
    ROUND(SUM(line_profit) / 1000000, 1) AS profit_m,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(net_sales) / COUNT(DISTINCT order_id), 0) AS aov
FROM stg_fact_orders
WHERE is_revenue = 1;

-- OTIF / perfect order (order grain = min of line flags)
SELECT
    ROUND(100.0 * AVG(otif), 1) AS otif_pct,
    ROUND(100.0 * AVG(perfect), 1) AS perfect_order_pct
FROM (
    SELECT
        order_id,
        MIN(is_otif) AS otif,
        MIN(is_perfect_order) AS perfect
    FROM stg_fact_orders
    GROUP BY order_id
) o;

-- logistics
SELECT
    ROUND(SUM(freight_cost) / 1000000, 1) AS freight_m,
    ROUND(AVG(freight_cost), 0) AS cost_per_ship,
    ROUND(100.0 * AVG(is_late), 1) AS delay_rate_pct,
    ROUND(100.0 * AVG(is_advance), 1) AS expedite_pct,
    ROUND(SUM(co2_kg) / 1000, 1) AS co2_tonnes
FROM stg_fact_shipments;

-- inventory latest snapshot
SELECT
    date_key,
    ROUND(SUM(on_hand_value) / 1000000, 1) AS on_hand_m,
    ROUND(SUM(on_hand_units), 0) AS on_hand_units
FROM stg_fact_inventory
WHERE date_key = (SELECT MAX(date_key) FROM stg_fact_inventory)
GROUP BY date_key;

-- procurement
SELECT
    COUNT(*) AS po_count,
    ROUND(SUM(po_value) / 1000000, 1) AS po_spend_m,
    ROUND(AVG(sla_days), 0) AS avg_sla_days,
    ROUND(100.0 * AVG(is_on_time_receipt), 1) AS on_time_receipt_pct
FROM stg_fact_procurement;

-- warehouse OTIF scorecard
SELECT
    warehouse_key,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(100.0 * AVG(is_otif), 1) AS otif_pct,
    ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_m
FROM stg_fact_orders
GROUP BY warehouse_key
ORDER BY orders DESC;

-- transport mode mix
SELECT
    transport_mode_key,
    COUNT(*) AS shipments,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct,
    ROUND(100.0 * AVG(is_late), 1) AS late_pct,
    ROUND(SUM(freight_cost), 0) AS freight
FROM stg_fact_shipments
GROUP BY transport_mode_key
ORDER BY shipments DESC;
