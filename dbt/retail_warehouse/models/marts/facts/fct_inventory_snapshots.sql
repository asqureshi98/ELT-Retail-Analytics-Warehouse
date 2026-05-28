select
    inventory_id,
    product_id,
    store_id,
    snapshot_date,
    quantity_on_hand,
    reorder_level,
    restock_quantity,
    case
        when quantity_on_hand <= reorder_level then true
        else false
    end as needs_restock
from {{ ref('stg_inventory') }}
