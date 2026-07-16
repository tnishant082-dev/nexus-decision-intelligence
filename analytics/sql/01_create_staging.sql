-- Staging for supply chain control tower (load from parquet/CSV exports)
-- MySQL / ANSI-friendly

CREATE TABLE IF NOT EXISTS stg_fact_orders (
    order_line_key       BIGINT PRIMARY KEY,
    order_item_id        BIGINT,
    order_id             BIGINT,
    order_date_key       INT,
    order_ts             DATETIME,
    customer_key         INT,
    product_key          INT,
    region_key           INT,
    warehouse_key        INT,
    vendor_key           INT,
    transport_mode_key   INT,
    carrier_key          INT,
    order_status_key     INT,
    payment_type_key     INT,
    source_system_key    INT,
    quantity             INT,
    unit_price           DECIMAL(12,4),
    gross_sales          DECIMAL(14,4),
    discount_amount      DECIMAL(12,4),
    discount_rate        DECIMAL(8,4),
    net_sales            DECIMAL(14,4),
    line_profit          DECIMAL(14,4),
    profit_ratio         DECIMAL(8,4),
    cogs_amount          DECIMAL(14,4),
    days_ship_real       INT,
    is_canceled          TINYINT,
    is_fraud             TINYINT,
    is_revenue           TINYINT,
    is_late              TINYINT,
    is_on_time           TINYINT,
    is_otif              TINYINT,
    is_perfect_order     TINYINT
);

CREATE TABLE IF NOT EXISTS stg_fact_shipments (
    shipment_key         BIGINT PRIMARY KEY,
    order_id             BIGINT,
    order_date_key       INT,
    ship_date_key        INT,
    warehouse_key        INT,
    transport_mode_key   INT,
    carrier_key          INT,
    delivery_status_key  INT,
    days_ship_real       INT,
    days_ship_scheduled  INT,
    days_delay           INT,
    is_late              TINYINT,
    is_on_time           TINYINT,
    is_advance           TINYINT,
    is_otif              TINYINT,
    is_perfect_order     TINYINT,
    line_count           INT,
    unit_count           INT,
    net_sales_amount     DECIMAL(14,4),
    freight_cost         DECIMAL(12,4),
    delay_cost           DECIMAL(12,4),
    co2_kg               DECIMAL(12,4),
    distance_km_proxy    DECIMAL(12,2)
);

CREATE TABLE IF NOT EXISTS stg_fact_inventory (
    inventory_key   BIGINT PRIMARY KEY,
    date_key        INT,
    product_key     INT,
    warehouse_key   INT,
    vendor_key      INT,
    on_hand_units   DECIMAL(14,4),
    on_hand_value   DECIMAL(14,4),
    receipts_units  DECIMAL(14,4),
    issues_units    DECIMAL(14,4),
    demand_units    DECIMAL(14,4),
    unfilled_units  DECIMAL(14,4)
);

CREATE TABLE IF NOT EXISTS stg_fact_procurement (
    po_line_key          BIGINT PRIMARY KEY,
    po_date_key          INT,
    promised_date_key    INT,
    product_key          INT,
    vendor_key           INT,
    warehouse_key        INT,
    po_number            VARCHAR(40),
    ordered_units        DECIMAL(14,4),
    received_units       DECIMAL(14,4),
    po_value             DECIMAL(14,4),
    sla_days             INT,
    is_on_time_receipt   TINYINT,
    source_class         VARCHAR(20)
);

CREATE OR REPLACE VIEW v_revenue_orders AS
SELECT *
FROM stg_fact_orders
WHERE is_revenue = 1;
