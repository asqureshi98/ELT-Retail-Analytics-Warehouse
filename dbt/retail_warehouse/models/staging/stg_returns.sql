select
    return_id,
    order_id,
    order_item_id,
    product_id,
    return_date::timestamp        as return_date,
    return_reason,
    refund_amount::numeric(12,2)  as refund_amount
from {{ source('raw', 'returns') }}
