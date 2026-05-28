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

## Future Warehouse Layers

Sprint 2 will add:

- staging models for type cleanup and standardization
- intermediate models for reusable business logic
- dimension tables: customers, products, stores, dates, promotions
- fact tables: sales, order items, payments, returns, inventory snapshots
