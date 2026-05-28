from pathlib import Path
import pandas as pd

from scripts.generate_retail_data import generate_retail_data


EXPECTED_FILES = {
    "customers.csv",
    "products.csv",
    "stores.csv",
    "promotions.csv",
    "orders.csv",
    "order_items.csv",
    "payments.csv",
    "inventory.csv",
    "returns.csv",
}


def test_generate_retail_data_writes_all_csvs_with_valid_relationships(tmp_path):
    generate_retail_data(
        orders=50,
        customers=20,
        products=10,
        stores=3,
        output_dir=tmp_path,
        seed=123,
    )

    generated = {path.name for path in tmp_path.glob("*.csv")}
    assert EXPECTED_FILES == generated

    customers = pd.read_csv(tmp_path / "customers.csv")
    products = pd.read_csv(tmp_path / "products.csv")
    stores = pd.read_csv(tmp_path / "stores.csv")
    orders = pd.read_csv(tmp_path / "orders.csv")
    order_items = pd.read_csv(tmp_path / "order_items.csv")
    payments = pd.read_csv(tmp_path / "payments.csv")
    inventory = pd.read_csv(tmp_path / "inventory.csv")
    returns = pd.read_csv(tmp_path / "returns.csv")

    assert len(orders) == 50
    assert len(customers) == 20
    assert len(products) == 10
    assert len(stores) == 3
    assert len(order_items) >= len(orders)
    assert set(orders["customer_id"]).issubset(set(customers["customer_id"]))
    assert set(orders["store_id"]).issubset(set(stores["store_id"]))
    assert set(order_items["order_id"]).issubset(set(orders["order_id"]))
    assert set(order_items["product_id"]).issubset(set(products["product_id"]))
    assert set(payments["order_id"]).issubset(set(orders["order_id"]))
    assert set(inventory["product_id"]).issubset(set(products["product_id"]))
    assert set(inventory["store_id"]).issubset(set(stores["store_id"]))
    if not returns.empty:
        assert set(returns["order_item_id"]).issubset(set(order_items["order_item_id"]))
        assert (returns["refund_amount"] >= 0).all()

    assert (products["unit_price"] > products["unit_cost"]).all()
    assert (order_items["quantity"] > 0).all()
    assert (order_items["line_total"] >= 0).all()
