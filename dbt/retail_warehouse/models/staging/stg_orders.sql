select
    order_id,
    customer_id,
    store_id,
    order_date::timestamp         as order_date,
    order_status,
    nullif(promotion_id, '')      as promotion_id,
    subtotal_amount::numeric(12,2)  as subtotal_amount,
    discount_amount::numeric(12,2)  as discount_amount,
    tax_amount::numeric(12,2)       as tax_amount,
    shipping_amount::numeric(12,2)  as shipping_amount,
    total_amount::numeric(12,2)     as total_amount
from {{ source('raw', 'orders') }}
