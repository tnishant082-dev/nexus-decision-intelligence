-- NEXUS warehouse views (also created by data-engineering/etl/warehouse.py)
-- Reference copies for analysts

-- Executive
SELECT * FROM v_exec_kpis;

-- OTIF at order grain
SELECT * FROM v_otif_order;

-- Logistics
SELECT * FROM v_logistics;

-- Category-week demand
SELECT * FROM v_demand_weekly LIMIT 100;

-- Late % by warehouse
SELECT w.warehouse_name,
       ROUND(AVG(o.is_late)*100,2) AS late_pct,
       ROUND(AVG(o.is_otif)*100,2) AS otif_pct,
       COUNT(*) AS lines
FROM fact_orders o
JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
GROUP BY 1
ORDER BY late_pct DESC;
