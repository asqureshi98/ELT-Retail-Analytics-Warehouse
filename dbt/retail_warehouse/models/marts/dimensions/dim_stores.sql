select
    store_id,
    store_name,
    channel,
    city,
    state,
    country,
    opened_at
from {{ ref('stg_stores') }}
