select
    product_id,
    sku,
    product_name,
    category,
    subcategory,
    brand,
    unit_cost::numeric(12,2)      as unit_cost,
    unit_price::numeric(12,2)     as unit_price,
    is_active::boolean            as is_active
from {{ source('raw', 'products') }}
