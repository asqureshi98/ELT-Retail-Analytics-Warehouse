{{ config(materialized='table') }}

with spine as (
    select generate_series(
        '2020-01-01'::date,
        '2030-12-31'::date,
        '1 day'::interval
    )::date as date_day
)
select
    date_day,
    date_part('year', date_day)::integer                        as year,
    date_part('quarter', date_day)::integer                     as quarter,
    date_part('month', date_day)::integer                       as month,
    trim(to_char(date_day, 'Month'))                            as month_name,
    date_part('week', date_day)::integer                        as week_of_year,
    date_part('dow', date_day)::integer                         as day_of_week,
    trim(to_char(date_day, 'Day'))                              as day_name,
    case
        when date_part('dow', date_day) in (0, 6) then true
        else false
    end                                                         as is_weekend
from spine
