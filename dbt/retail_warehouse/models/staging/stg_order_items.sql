select
    order_item_id,
    order_id,
    product_id,
    quantity::integer             as quantity,
    unit_price::numeric(12,2)     as unit_price,
    unit_cost::numeric(12,2)      as unit_cost,
    discount_amount::numeric(12,2) as discount_amount,
    line_total::numeric(12,2)     as line_total
from {{ source('raw', 'order_items') }}
