select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    gender,
    date_of_birth::date           as date_of_birth,
    city,
    state,
    country,
    created_at::timestamp         as created_at
from {{ source('raw', 'customers') }}
