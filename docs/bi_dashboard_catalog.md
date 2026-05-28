# Sprint 4 BI Dashboard Catalog

This document defines the local-first Metabase BI layer for the retail analytics warehouse. Dashboards are provisioned with `make metabase-provision` from native SQL cards that query dbt marts in the `marts` schema.

## Local Metabase defaults

- URL: `http://localhost:3000`
- Default local admin: `admin@retail-analytics.local` / `RetailLocalAdmin!2026`
- Collection: `Retail Analytics`
- Warehouse database in Metabase: `Retail Warehouse`
- Metabase-to-Postgres host: `postgres` (Docker Compose service hostname)
- Host-to-Metabase URL: `localhost:3000`

These credentials are development-only defaults and can be overridden through environment variables documented in `docs/runbook.md`.

## Core metric definitions

| Metric | Definition | Primary marts |
| --- | --- | --- |
| Orders | `count(*)` from `marts.fct_sales` | `fct_sales` |
| Paid orders | `count(*) filter (where is_paid)` | `fct_sales` |
| Gross sales | `sum(total_amount)` before refunds | `fct_sales` |
| Discounts | `sum(discount_amount)` | `fct_sales` |
| Refunds | `sum(total_refund_amount)` or `sum(refund_amount)` | `fct_sales`, `fct_returns` |
| Net sales | `sum(total_amount) - sum(total_refund_amount)` | `fct_sales` |
| Average order value | `avg(total_amount)` | `fct_sales` |
| Units sold | `sum(quantity)` | `fct_order_items` |
| Gross profit | `sum(gross_profit)` | `fct_order_items` |
| Gross margin percent | `sum(gross_profit) / nullif(sum(revenue), 0)` | `fct_order_items` |
| Return rate | `returned_orders / total_orders` | `fct_sales` |
| Products needing restock | `count(*) filter (where needs_restock)` | `fct_inventory_snapshots` |
| Suggested restock units | `sum(restock_quantity) filter (where needs_restock)` | `fct_inventory_snapshots` |
| Customer lifetime net sales | `sum(total_amount) - sum(total_refund_amount)` grouped by customer | `fct_sales`, `dim_customers` |

## Dashboard catalog

### 1. Executive Sales Overview

Business questions:
- How much revenue is the retail business generating?
- Are refunds materially reducing gross sales?
- What is the daily sales trend?
- Are payment statuses healthy?

Required marts:
- `marts.fct_sales`

Provisioned cards:
- `Executive KPI Summary`
- `Daily Net Sales Trend`
- `Payment Status Mix`

Representative SQL:

```sql
select
    count(*) as orders,
    count(*) filter (where is_paid) as paid_orders,
    round(sum(total_amount)::numeric, 2) as gross_sales,
    round(sum(total_refund_amount)::numeric, 2) as refunds,
    round((sum(total_amount) - sum(total_refund_amount))::numeric, 2) as net_sales,
    round(avg(total_amount)::numeric, 2) as average_order_value
from marts.fct_sales;
```

### 2. Product and Category Performance

Business questions:
- Which categories and products drive revenue?
- Which categories have the healthiest gross margin?
- Which brands/products should merchandising prioritize?

Required marts:
- `marts.fct_order_items`
- `marts.dim_products`

Provisioned cards:
- `Category Revenue and Margin`
- `Top Products by Revenue`

Representative SQL:

```sql
select
    category,
    round(sum(revenue)::numeric, 2) as revenue,
    round(sum(gross_profit)::numeric, 2) as gross_profit,
    round((sum(gross_profit) / nullif(sum(revenue), 0))::numeric, 4) as gross_margin_pct,
    sum(quantity) as units_sold
from marts.fct_order_items
group by category
order by revenue desc;
```

### 3. Store and Channel Performance

Business questions:
- Which stores and channels produce the most net sales?
- How does average order value differ by channel?
- Which locations need operational review?

Required marts:
- `marts.fct_sales`
- `marts.dim_stores`

Provisioned cards:
- `Store Channel Sales`
- `Top Stores by Net Sales`

Representative SQL:

```sql
select
    s.channel,
    count(*) as orders,
    round(sum(f.total_amount)::numeric, 2) as gross_sales,
    round(avg(f.total_amount)::numeric, 2) as average_order_value
from marts.fct_sales f
join marts.dim_stores s on f.store_id = s.store_id
group by s.channel
order by gross_sales desc;
```

### 4. Customer Behavior

Business questions:
- Where are customers concentrated?
- Who are the highest-value customers?
- Which customer segments are best candidates for retention campaigns?

Required marts:
- `marts.dim_customers`
- `marts.fct_sales`

Provisioned cards:
- `Customer Geography`
- `Customer Lifetime Value Leaders`

Representative SQL:

```sql
select
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    count(f.order_id) as orders,
    round((sum(f.total_amount) - sum(f.total_refund_amount))::numeric, 2) as lifetime_net_sales
from marts.fct_sales f
join marts.dim_customers c on f.customer_id = c.customer_id
group by c.customer_id, customer_name
order by lifetime_net_sales desc
limit 15;
```

### 5. Returns and Refunds

Business questions:
- What share of orders experience returns?
- Which return reasons drive refund exposure?
- Are returns trending up over time?

Required marts:
- `marts.fct_sales`
- `marts.fct_returns`

Provisioned cards:
- `Return Rate Summary`
- `Refunds by Return Reason`

Representative SQL:

```sql
select
    return_reason,
    count(*) as returns,
    round(sum(refund_amount)::numeric, 2) as refund_amount
from marts.fct_returns
group by return_reason
order by refund_amount desc;
```

### 6. Inventory Health

Business questions:
- Which stores have the most products below reorder thresholds?
- Which product/store pairs need restock attention?
- How many units are on hand and suggested for restock?

Required marts:
- `marts.fct_inventory_snapshots`
- `marts.dim_products`
- `marts.dim_stores`

Provisioned cards:
- `Restock Risk by Store`
- `Low Stock Products`

Representative SQL:

```sql
select
    s.store_name,
    s.channel,
    count(*) filter (where i.needs_restock) as products_needing_restock,
    sum(i.quantity_on_hand) as units_on_hand,
    sum(i.restock_quantity) filter (where i.needs_restock) as suggested_restock_units
from marts.fct_inventory_snapshots i
join marts.dim_stores s on i.store_id = s.store_id
group by s.store_name, s.channel
order by products_needing_restock desc, suggested_restock_units desc;
```

## Provisioning behavior

`scripts/provision_metabase.py` uses the Metabase HTTP API to:

1. Wait for `http://localhost:3000` to respond.
2. Complete first-run setup with local dev credentials when a setup token is present, or log in when Metabase is already configured.
3. Create or update the `Retail Warehouse` Postgres database connection using Docker hostname `postgres`.
4. Create or reuse the `Retail Analytics` collection.
5. Create or update native SQL cards by name.
6. Create or update dashboards by name.
7. Add missing cards to dashboards without duplicating cards that are already present.

Dashboard visual layout is intentionally simple and API-driven. The script provisions deterministic grid positions (`row`, `col`, `sizeX`, `sizeY`) for each card, but Metabase may adjust rendering details by image/API version. This Sprint 4 workflow was verified against the Docker image `metabase/metabase:latest` resolving locally to Metabase `v0.61.3`; that version accepts dashboard-card placement through `PUT /api/dashboard/{id}` with a `dashcards` payload rather than a separate `/cards` route.
