from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

CATEGORIES = {
    "Electronics": ["Phones", "Computers", "Accessories"],
    "Home": ["Kitchen", "Furniture", "Decor"],
    "Apparel": ["Men", "Women", "Kids"],
    "Grocery": ["Pantry", "Beverages", "Snacks"],
    "Beauty": ["Skincare", "Haircare", "Fragrance"],
}
PAYMENT_METHODS = ["card", "cash", "wallet", "bank_transfer"]
RETURN_REASONS = ["damaged", "late", "wrong_item", "changed_mind"]


def _money(value: float) -> float:
    return round(value, 2)


def generate_retail_data(
    orders: int,
    customers: int,
    products: int,
    stores: int,
    output_dir: str | Path,
    seed: int = 42,
) -> None:
    """Generate synthetic retail CSV files with referential integrity."""
    if min(orders, customers, products, stores) <= 0:
        raise ValueError("orders, customers, products, and stores must all be positive")

    random.seed(seed)
    fake = Faker()
    Faker.seed(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    customer_rows = []
    for idx in range(1, customers + 1):
        customer_rows.append(
            {
                "customer_id": f"C{idx:06d}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "phone": fake.phone_number(),
                "gender": random.choice(["female", "male", "non_binary", "prefer_not_to_say"]),
                "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": "USA",
                "created_at": fake.date_time_between(start_date="-3y", end_date="-30d").isoformat(sep=" "),
            }
        )
    customers_df = pd.DataFrame(customer_rows)

    store_rows = []
    for idx in range(1, stores + 1):
        channel = random.choice(["online", "physical", "marketplace"])
        store_rows.append(
            {
                "store_id": f"S{idx:04d}",
                "store_name": f"{fake.city()} {channel.title()} Store {idx}",
                "channel": channel,
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": "USA",
                "opened_at": fake.date_between(start_date="-8y", end_date="-1y").isoformat(),
            }
        )
    stores_df = pd.DataFrame(store_rows)

    product_rows = []
    for idx in range(1, products + 1):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        unit_cost = _money(random.uniform(2, 500))
        markup = random.uniform(1.15, 2.8)
        unit_price = _money(unit_cost * markup)
        product_rows.append(
            {
                "product_id": f"P{idx:06d}",
                "sku": f"SKU-{idx:06d}",
                "product_name": f"{fake.word().title()} {subcategory} Item {idx}",
                "category": category,
                "subcategory": subcategory,
                "brand": fake.company(),
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "is_active": random.choice([True, True, True, False]),
            }
        )
    products_df = pd.DataFrame(product_rows)

    promotion_rows = []
    for idx in range(1, 16):
        start = fake.date_between(start_date="-18M", end_date="today")
        end = start + timedelta(days=random.randint(7, 45))
        promotion_rows.append(
            {
                "promotion_id": f"PR{idx:04d}",
                "promotion_name": f"{fake.catch_phrase()} Promo {idx}",
                "promotion_type": random.choice(["percentage", "fixed_amount", "bogo"]),
                "discount_value": _money(random.choice([5, 10, 15, 20, 25])),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "is_active": end >= datetime.utcnow().date(),
            }
        )
    promotions_df = pd.DataFrame(promotion_rows)

    order_rows = []
    order_item_rows = []
    payment_rows = []
    return_rows = []
    product_records = products_df.to_dict("records")
    base_date = datetime.utcnow() - timedelta(days=365)

    for order_idx in range(1, orders + 1):
        order_id = f"O{order_idx:08d}"
        customer_id = random.choice(customer_rows)["customer_id"]
        store_id = random.choice(store_rows)["store_id"]
        order_date = base_date + timedelta(days=random.randint(0, 364), seconds=random.randint(0, 86399))
        order_status = random.choices(["completed", "cancelled", "returned"], weights=[88, 7, 5], k=1)[0]
        promo = random.choice(promotion_rows) if random.random() < 0.25 else None
        promotion_id = promo["promotion_id"] if promo else ""

        item_count = random.randint(1, 5)
        selected_products = random.sample(product_records, k=min(item_count, len(product_records)))
        subtotal = 0.0
        order_discount = 0.0
        order_item_ids = []

        for item_number, product in enumerate(selected_products, start=1):
            quantity = random.randint(1, 4)
            unit_price = float(product["unit_price"])
            unit_cost = float(product["unit_cost"])
            gross = quantity * unit_price
            item_discount = _money(gross * random.uniform(0.03, 0.15)) if promo else 0.0
            line_total = _money(gross - item_discount)
            order_item_id = f"OI{order_idx:08d}_{item_number}"
            order_item_ids.append((order_item_id, product["product_id"], line_total, order_status))
            subtotal += gross
            order_discount += item_discount
            order_item_rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": _money(unit_price),
                    "unit_cost": _money(unit_cost),
                    "discount_amount": _money(item_discount),
                    "line_total": line_total,
                }
            )

        subtotal = _money(subtotal)
        order_discount = _money(order_discount)
        taxable_amount = max(subtotal - order_discount, 0)
        tax_amount = _money(taxable_amount * 0.0825)
        shipping_amount = _money(random.choice([0, 4.99, 7.99, 12.99]))
        total_amount = _money(taxable_amount + tax_amount + shipping_amount)

        order_rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "store_id": store_id,
                "order_date": order_date.isoformat(sep=" "),
                "order_status": order_status,
                "promotion_id": promotion_id,
                "subtotal_amount": subtotal,
                "discount_amount": order_discount,
                "tax_amount": tax_amount,
                "shipping_amount": shipping_amount,
                "total_amount": total_amount,
            }
        )

        paid = order_status != "cancelled"
        payment_status = "paid" if paid else "failed"
        if order_status == "returned":
            payment_status = "refunded"
        payment_rows.append(
            {
                "payment_id": f"PAY{order_idx:08d}",
                "order_id": order_id,
                "payment_method": random.choice(PAYMENT_METHODS),
                "payment_status": payment_status,
                "payment_amount": total_amount if paid else 0.0,
                "paid_at": (order_date + timedelta(minutes=random.randint(1, 60))).isoformat(sep=" "),
            }
        )

        if order_status == "returned" or random.random() < 0.03:
            returned_item_id, returned_product_id, line_total, _ = random.choice(order_item_ids)
            return_rows.append(
                {
                    "return_id": f"R{len(return_rows) + 1:08d}",
                    "order_id": order_id,
                    "order_item_id": returned_item_id,
                    "product_id": returned_product_id,
                    "return_date": (order_date + timedelta(days=random.randint(1, 30))).isoformat(sep=" "),
                    "return_reason": random.choice(RETURN_REASONS),
                    "refund_amount": _money(line_total * random.uniform(0.5, 1.0)),
                }
            )

    inventory_rows = []
    snapshot_date = datetime.utcnow().date().isoformat()
    inv_id = 1
    for store in store_rows:
        for product in random.sample(product_records, k=min(len(product_records), max(1, int(len(product_records) * 0.35)))):
            reorder_level = random.randint(5, 30)
            quantity = random.randint(0, 200)
            inventory_rows.append(
                {
                    "inventory_id": f"INV{inv_id:08d}",
                    "product_id": product["product_id"],
                    "store_id": store["store_id"],
                    "snapshot_date": snapshot_date,
                    "quantity_on_hand": quantity,
                    "reorder_level": reorder_level,
                    "restock_quantity": random.randint(25, 150),
                }
            )
            inv_id += 1

    outputs = {
        "customers.csv": customers_df,
        "products.csv": products_df,
        "stores.csv": stores_df,
        "promotions.csv": promotions_df,
        "orders.csv": pd.DataFrame(order_rows),
        "order_items.csv": pd.DataFrame(order_item_rows),
        "payments.csv": pd.DataFrame(payment_rows),
        "inventory.csv": pd.DataFrame(inventory_rows),
        "returns.csv": pd.DataFrame(return_rows, columns=["return_id", "order_id", "order_item_id", "product_id", "return_date", "return_reason", "refund_amount"]),
    }
    for filename, df in outputs.items():
        df.to_csv(output_path / filename, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic retail CSV files.")
    parser.add_argument("--orders", type=int, default=10_000)
    parser.add_argument("--customers", type=int, default=1_000)
    parser.add_argument("--products", type=int, default=250)
    parser.add_argument("--stores", type=int, default=10)
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_retail_data(args.orders, args.customers, args.products, args.stores, args.output_dir, args.seed)
    print(f"Generated retail data in {args.output_dir}")


if __name__ == "__main__":
    main()
