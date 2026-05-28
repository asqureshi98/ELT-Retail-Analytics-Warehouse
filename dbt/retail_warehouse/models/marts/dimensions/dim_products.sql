select
    product_id,
    sku,
    product_name,
    category,
    subcategory,
    brand,
    unit_cost,
    unit_price,
    is_active,
    case
        when unit_price = 0 then null
        else round((unit_price - unit_cost) / unit_price, 4)
    end as gross_margin_pct
from {{ ref('stg_products') }}
