select
    payment_id,
    order_id,
    payment_method,
    payment_status,
    payment_amount::numeric(12,2) as payment_amount,
    paid_at::timestamp            as paid_at
from {{ source('raw', 'payments') }}
