select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    gender,
    date_of_birth,
    city,
    state,
    country,
    created_at,
    date_part('year', age(current_date, date_of_birth))::integer as customer_age_years
from {{ ref('stg_customers') }}
