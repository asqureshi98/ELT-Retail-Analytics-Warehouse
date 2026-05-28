select
    promotion_id,
    promotion_name,
    promotion_type,
    discount_value::numeric(12,2) as discount_value,
    start_date::date              as start_date,
    end_date::date                as end_date,
    is_active::boolean            as is_active
from {{ source('raw', 'promotions') }}
