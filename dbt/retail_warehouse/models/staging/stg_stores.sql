select
    store_id,
    store_name,
    channel,
    city,
    state,
    country,
    opened_at::date               as opened_at
from {{ source('raw', 'stores') }}
