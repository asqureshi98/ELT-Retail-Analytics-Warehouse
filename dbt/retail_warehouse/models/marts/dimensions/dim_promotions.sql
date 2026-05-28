select
    promotion_id,
    promotion_name,
    promotion_type,
    discount_value,
    start_date,
    end_date,
    is_active
from {{ ref('stg_promotions') }}
