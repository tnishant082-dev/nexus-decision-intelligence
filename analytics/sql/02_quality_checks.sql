-- fact row counts
SELECT 'orders' AS tbl, COUNT(*) AS n FROM stg_fact_orders
UNION ALL SELECT 'shipments', COUNT(*) FROM stg_fact_shipments
UNION ALL SELECT 'inventory', COUNT(*) FROM stg_fact_inventory
UNION ALL SELECT 'procurement', COUNT(*) FROM stg_fact_procurement;

-- revenue vs cancelled / fraud mix
SELECT
    SUM(is_revenue) AS revenue_lines,
    SUM(is_canceled) AS canceled_lines,
    SUM(is_fraud) AS fraud_lines,
    COUNT(*) AS all_lines
FROM stg_fact_orders;

-- unknown dimension keys on orders
SELECT
    SUM(CASE WHEN vendor_key < 0 THEN 1 ELSE 0 END) AS unk_vendor,
    SUM(CASE WHEN warehouse_key < 0 THEN 1 ELSE 0 END) AS unk_warehouse,
    SUM(CASE WHEN product_key < 0 THEN 1 ELSE 0 END) AS unk_product
FROM stg_fact_orders;

-- shipment delay distribution
SELECT
    SUM(is_late) AS late_shipments,
    SUM(is_advance) AS early_shipments,
    ROUND(AVG(days_delay), 2) AS avg_days_delay,
    ROUND(100.0 * AVG(is_otif), 1) AS otif_pct
FROM stg_fact_shipments;

-- inventory negatives / zeros
SELECT
    SUM(CASE WHEN on_hand_units < 0 THEN 1 ELSE 0 END) AS negative_on_hand,
    SUM(CASE WHEN on_hand_units = 0 THEN 1 ELSE 0 END) AS zero_on_hand,
    COUNT(DISTINCT date_key) AS snapshot_days
FROM stg_fact_inventory;

-- PO receipt SLA hit rate
SELECT
    COUNT(*) AS po_lines,
    ROUND(100.0 * AVG(is_on_time_receipt), 1) AS on_time_receipt_pct,
    ROUND(SUM(po_value), 0) AS po_spend
FROM stg_fact_procurement;
