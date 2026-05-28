with order_items as (
    select * from {{ ref('stg_order_items') }}
),
products as (
    select
        product_id,
        product_name,
        category,
        subcategory,
        brand,
        unit_cost as product_unit_cost,
        unit_price as product_unit_price
    from {{ ref('stg_products') }}
)
select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.brand,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.discount_amount,
    oi.line_total,
    oi.line_total                                               as revenue,
    round(oi.unit_cost * oi.quantity, 2)                       as cost,
    round(oi.line_total - (oi.unit_cost * oi.quantity), 2)     as gross_profit,
    case
        when oi.unit_price = 0 then null
        else round(
            (oi.unit_price - oi.unit_cost) / oi.unit_price * 100, 2
        )
    end                                                         as gross_margin_pct
from order_items oi
inner join products p on oi.product_id = p.product_id
