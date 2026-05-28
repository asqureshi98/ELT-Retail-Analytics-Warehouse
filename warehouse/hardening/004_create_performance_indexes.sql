-- Sprint 6 local warehouse performance hardening.
-- Idempotent indexes for common ELT joins, dashboard filters, and quality checks.

CREATE INDEX IF NOT EXISTS idx_raw_orders_order_id ON raw.orders (order_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_customer_id ON raw.orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_store_id ON raw.orders (store_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_order_date ON raw.orders (order_date);
CREATE INDEX IF NOT EXISTS idx_raw_orders_promotion_id ON raw.orders (promotion_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_order_item_id ON raw.order_items (order_item_id);
CREATE INDEX IF NOT EXISTS idx_raw_order_items_order_id ON raw.order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_raw_order_items_product_id ON raw.order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_raw_payments_payment_id ON raw.payments (payment_id);
CREATE INDEX IF NOT EXISTS idx_raw_payments_order_id ON raw.payments (order_id);
CREATE INDEX IF NOT EXISTS idx_raw_returns_return_id ON raw.returns (return_id);
CREATE INDEX IF NOT EXISTS idx_raw_returns_order_id ON raw.returns (order_id);
CREATE INDEX IF NOT EXISTS idx_raw_returns_order_item_id ON raw.returns (order_item_id);
CREATE INDEX IF NOT EXISTS idx_raw_inventory_product_store_date ON raw.inventory (product_id, store_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_raw_products_product_id ON raw.products (product_id);
CREATE INDEX IF NOT EXISTS idx_raw_customers_customer_id ON raw.customers (customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_stores_store_id ON raw.stores (store_id);
CREATE INDEX IF NOT EXISTS idx_raw_promotions_promotion_id ON raw.promotions (promotion_id);

CREATE INDEX IF NOT EXISTS idx_audit_file_loads_loaded_at ON audit.file_loads (loaded_at);
CREATE INDEX IF NOT EXISTS idx_audit_file_loads_status ON audit.file_loads (status);
CREATE INDEX IF NOT EXISTS idx_audit_batch_runs_status ON audit.batch_runs (status);

CREATE INDEX IF NOT EXISTS idx_marts_fct_sales_order_id ON marts.fct_sales (order_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_sales_order_date_day ON marts.fct_sales (order_date_day);
CREATE INDEX IF NOT EXISTS idx_marts_fct_sales_customer_id ON marts.fct_sales (customer_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_sales_store_id ON marts.fct_sales (store_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_order_items_order_id ON marts.fct_order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_order_items_product_id ON marts.fct_order_items (product_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_returns_order_id ON marts.fct_returns (order_id);
CREATE INDEX IF NOT EXISTS idx_marts_fct_payments_order_id ON marts.fct_payments (order_id);
CREATE INDEX IF NOT EXISTS idx_marts_inventory_product_store_date ON marts.fct_inventory_snapshots (product_id, store_id, snapshot_date);
