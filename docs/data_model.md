# Data Model

## Source Entities

Sprint 1 generates and loads these raw source entities:

- customers
- products
- stores
- promotions
- orders
- order_items
- payments
- inventory
- returns

## Raw Layer

The raw layer stores source-shaped data loaded from local CSV files. Raw tables intentionally avoid strict constraints so files can be loaded and inspected even when downstream quality checks fail.

## Core Relationships

- `orders.customer_id` references `customers.customer_id`
- `orders.store_id` references `stores.store_id`
- `orders.promotion_id` optionally references `promotions.promotion_id`
- `order_items.order_id` references `orders.order_id`
- `order_items.product_id` references `products.product_id`
- `payments.order_id` references `orders.order_id`
- `inventory.product_id` references `products.product_id`
- `inventory.store_id` references `stores.store_id`
- `returns.order_id` references `orders.order_id`
- `returns.order_item_id` references `order_items.order_item_id`
- `returns.product_id` references `products.product_id`

## Staging Layer

Sprint 2 adds 9 staging models, one per raw source. Each model casts string columns to their correct types (dates, timestamps, numerics, booleans, integers) and normalises names. No business logic lives in staging.

- `stg_customers`: casts `date_of_birth` to date and `created_at` to timestamp.
- `stg_products`: casts `unit_cost` and `unit_price` to numeric(12,2), `is_active` to boolean.
- `stg_stores`: casts `opened_at` to date.
- `stg_promotions`: casts `discount_value` to numeric(12,2), `start_date`/`end_date` to date, `is_active` to boolean.
- `stg_orders`: casts monetary columns to numeric(12,2), `order_date` to timestamp, and applies `nullif(promotion_id, '')` to normalise empty-string promotions to NULL.
- `stg_order_items`: casts `quantity` to integer, monetary columns to numeric(12,2).
- `stg_payments`: casts `payment_amount` to numeric(12,2), `paid_at` to timestamp.
- `stg_inventory`: casts `snapshot_date` to date, count columns to integer.
- `stg_returns`: casts `return_date` to timestamp, `refund_amount` to numeric(12,2).

## Intermediate Layer

Two intermediate models implement reusable business rules that are consumed by multiple mart models.

- `int_order_items_enriched`: joins order items with product attributes; adds `revenue`, `cost`, `gross_profit`, and `gross_margin_pct` margin fields.
- `int_orders_with_payment_status`: joins orders with payments and a return aggregate; adds `is_paid` boolean, `has_return` boolean, `return_count`, and `total_refund_amount`.

## Dimensions

Five dimension tables are built as materialised tables in the `marts` schema.

- `dim_customers`: all customer attributes plus a derived `customer_age_years` field using `age(current_date, date_of_birth)`.
- `dim_products`: all product attributes plus a derived `gross_margin_pct` field.
- `dim_stores`: store attributes including `channel` and location columns.
- `dim_promotions`: promotion attributes including type, discount value, and active date range.
- `dim_date`: date spine from 2020-01-01 to 2030-12-31 built with PostgreSQL `generate_series`; includes year, quarter, month, month_name, week_of_year, day_of_week, day_name, and `is_weekend` flag.

## Facts

Five fact tables are built as materialised tables in the `marts` schema.

- `fct_sales`: order grain; sourced from `int_orders_with_payment_status` joined to all four dimension tables; contains order amounts, payment attributes, and return summary fields.
- `fct_order_items`: order item grain; sourced from `int_order_items_enriched`; contains revenue, cost, gross profit, and margin fields at the line level.
- `fct_payments`: payment grain; sourced directly from `stg_payments`.
- `fct_returns`: return grain; sourced directly from `stg_returns`.
- `fct_inventory_snapshots`: inventory snapshot grain; sourced from `stg_inventory`; adds a `needs_restock` boolean flag when `quantity_on_hand <= reorder_level`.
