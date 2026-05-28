{% snapshot snap_customers %}

{{
  config(
    target_schema='snapshots',
    unique_key='customer_id',
    strategy='timestamp',
    updated_at='created_at',
    invalidate_hard_deletes=True
  )
}}

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
    created_at
from {{ source('raw', 'customers') }}

{% endsnapshot %}
