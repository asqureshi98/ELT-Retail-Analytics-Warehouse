select
    return_id,
    order_id,
    order_item_id,
    product_id,
    return_date,
    return_reason,
    refund_amount
from {{ ref('stg_returns') }}
