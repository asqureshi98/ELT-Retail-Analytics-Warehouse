select
    payment_id,
    order_id,
    payment_method,
    payment_status,
    payment_amount,
    paid_at
from {{ ref('stg_payments') }}
