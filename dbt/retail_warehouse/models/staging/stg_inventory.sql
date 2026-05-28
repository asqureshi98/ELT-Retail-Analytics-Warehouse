select
    inventory_id,
    product_id,
    store_id,
    snapshot_date::date           as snapshot_date,
    quantity_on_hand::integer     as quantity_on_hand,
    reorder_level::integer        as reorder_level,
    restock_quantity::integer     as restock_quantity
from {{ source('raw', 'inventory') }}
