CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    gender TEXT,
    date_of_birth DATE,
    city TEXT,
    state TEXT,
    country TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id TEXT,
    sku TEXT,
    product_name TEXT,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    unit_cost NUMERIC(12, 2),
    unit_price NUMERIC(12, 2),
    is_active BOOLEAN
);

CREATE TABLE IF NOT EXISTS raw.stores (
    store_id TEXT,
    store_name TEXT,
    channel TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    opened_at DATE
);

CREATE TABLE IF NOT EXISTS raw.promotions (
    promotion_id TEXT,
    promotion_name TEXT,
    promotion_type TEXT,
    discount_value NUMERIC(12, 2),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN
);

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id TEXT,
    customer_id TEXT,
    store_id TEXT,
    order_date TIMESTAMP,
    order_status TEXT,
    promotion_id TEXT,
    subtotal_amount NUMERIC(12, 2),
    discount_amount NUMERIC(12, 2),
    tax_amount NUMERIC(12, 2),
    shipping_amount NUMERIC(12, 2),
    total_amount NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id TEXT,
    order_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    unit_price NUMERIC(12, 2),
    unit_cost NUMERIC(12, 2),
    discount_amount NUMERIC(12, 2),
    line_total NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS raw.payments (
    payment_id TEXT,
    order_id TEXT,
    payment_method TEXT,
    payment_status TEXT,
    payment_amount NUMERIC(12, 2),
    paid_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.inventory (
    inventory_id TEXT,
    product_id TEXT,
    store_id TEXT,
    snapshot_date DATE,
    quantity_on_hand INTEGER,
    reorder_level INTEGER,
    restock_quantity INTEGER
);

CREATE TABLE IF NOT EXISTS raw.returns (
    return_id TEXT,
    order_id TEXT,
    order_item_id TEXT,
    product_id TEXT,
    return_date TIMESTAMP,
    return_reason TEXT,
    refund_amount NUMERIC(12, 2)
);
