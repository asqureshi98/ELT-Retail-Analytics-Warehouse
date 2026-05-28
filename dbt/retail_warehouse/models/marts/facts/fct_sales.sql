select
    o.order_id,
    o.customer_id,
    o.store_id,
    d.date_day                           as order_date_day,
    o.order_date,
    o.order_status,
    o.promotion_id,
    o.subtotal_amount,
    o.discount_amount,
    o.tax_amount,
    o.shipping_amount,
    o.total_amount,
    o.payment_status,
    o.payment_method,
    o.payment_amount,
    o.paid_at,
    o.is_paid,
    o.has_return,
    o.return_count,
    o.total_refund_amount
from {{ ref('int_orders_with_payment_status') }} o
inner join {{ ref('dim_customers') }} c  on o.customer_id     = c.customer_id
inner join {{ ref('dim_stores') }} s      on o.store_id        = s.store_id
inner join {{ ref('dim_date') }} d        on o.order_date::date = d.date_day
left  join {{ ref('dim_promotions') }} p  on o.promotion_id    = p.promotion_id
