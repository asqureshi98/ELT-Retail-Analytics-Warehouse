select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.product_name,
    oi.category,
    oi.subcategory,
    oi.brand,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.discount_amount,
    oi.line_total,
    oi.revenue,
    oi.cost,
    oi.gross_profit,
    oi.gross_margin_pct
from {{ ref('int_order_items_enriched') }} oi
