with orders as (
    select * from {{ ref('stg_orders') }}
),
payments as (
    select
        order_id,
        payment_status,
        payment_method,
        payment_amount,
        paid_at
    from {{ ref('stg_payments') }}
),
returns_agg as (
    select
        order_id,
        count(*)                    as return_count,
        sum(refund_amount)          as total_refund_amount
    from {{ ref('stg_returns') }}
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    o.store_id,
    o.order_date,
    o.order_status,
    o.promotion_id,
    o.subtotal_amount,
    o.discount_amount,
    o.tax_amount,
    o.shipping_amount,
    o.total_amount,
    p.payment_status,
    p.payment_method,
    p.payment_amount,
    p.paid_at,
    case when p.payment_status = 'paid' then true else false end as is_paid,
    case when r.order_id is not null then true else false end    as has_return,
    coalesce(r.return_count, 0)                                 as return_count,
    coalesce(r.total_refund_amount, 0.00)                       as total_refund_amount
from orders o
left join payments p on o.order_id = p.order_id
left join returns_agg r on o.order_id = r.order_id
