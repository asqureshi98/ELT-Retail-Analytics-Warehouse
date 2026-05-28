from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "customers.csv": ["customer_id", "first_name", "last_name", "email", "phone", "gender", "date_of_birth", "city", "state", "country", "created_at"],
    "products.csv": ["product_id", "sku", "product_name", "category", "subcategory", "brand", "unit_cost", "unit_price", "is_active"],
    "stores.csv": ["store_id", "store_name", "channel", "city", "state", "country", "opened_at"],
    "promotions.csv": ["promotion_id", "promotion_name", "promotion_type", "discount_value", "start_date", "end_date", "is_active"],
    "orders.csv": ["order_id", "customer_id", "store_id", "order_date", "order_status", "promotion_id", "subtotal_amount", "discount_amount", "tax_amount", "shipping_amount", "total_amount"],
    "order_items.csv": ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "unit_cost", "discount_amount", "line_total"],
    "payments.csv": ["payment_id", "order_id", "payment_method", "payment_status", "payment_amount", "paid_at"],
    "inventory.csv": ["inventory_id", "product_id", "store_id", "snapshot_date", "quantity_on_hand", "reorder_level", "restock_quantity"],
    "returns.csv": ["return_id", "order_id", "order_item_id", "product_id", "return_date", "return_reason", "refund_amount"],
}

ID_COLUMNS = {
    "customers.csv": ["customer_id"],
    "products.csv": ["product_id"],
    "stores.csv": ["store_id"],
    "promotions.csv": ["promotion_id"],
    "orders.csv": ["order_id", "customer_id", "store_id"],
    "order_items.csv": ["order_item_id", "order_id", "product_id"],
    "payments.csv": ["payment_id", "order_id"],
    "inventory.csv": ["inventory_id", "product_id", "store_id"],
    "returns.csv": ["return_id", "order_id", "order_item_id", "product_id"],
}

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def _check_required_files(input_dir: Path, errors: list[str]) -> None:
    for filename in REQUIRED_COLUMNS:
        if not (input_dir / filename).exists():
            errors.append(f"Missing required file: {filename}")


def _load_frames(input_dir: Path, errors: list[str]) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for filename, required_columns in REQUIRED_COLUMNS.items():
        path = input_dir / filename
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            errors.append(f"Could not read {filename}: {exc}")
            continue
        missing_columns = sorted(set(required_columns) - set(df.columns))
        if missing_columns:
            errors.append(f"{filename} missing required columns: {', '.join(missing_columns)}")
        if filename != "returns.csv" and df.empty:
            errors.append(f"{filename} is empty")
        for column in ID_COLUMNS[filename]:
            if column in df.columns and df[column].isna().any():
                errors.append(f"{filename}.{column} contains null values")
        frames[filename] = df
    return frames


def _check_subset(child: pd.Series, parent: pd.Series, label: str, errors: list[str]) -> None:
    child_values = set(child.dropna().astype(str))
    child_values.discard("")
    parent_values = set(parent.dropna().astype(str))
    missing = child_values - parent_values
    if missing:
        errors.append(f"{label} contains values not found in {label.split(' contains ')[0].split('.')[0]} parent")


def _check_relationships(frames: dict[str, pd.DataFrame], errors: list[str]) -> None:
    required = {"customers.csv", "products.csv", "stores.csv", "orders.csv", "order_items.csv", "payments.csv", "inventory.csv", "returns.csv"}
    if not required.issubset(frames):
        return
    customers = frames["customers.csv"]
    products = frames["products.csv"]
    stores = frames["stores.csv"]
    orders = frames["orders.csv"]
    order_items = frames["order_items.csv"]
    payments = frames["payments.csv"]
    inventory = frames["inventory.csv"]
    returns = frames["returns.csv"]

    checks = [
        (orders["customer_id"], customers["customer_id"], "orders.customer_id contains values not found in customers.customer_id"),
        (orders["store_id"], stores["store_id"], "orders.store_id contains values not found in stores.store_id"),
        (order_items["order_id"], orders["order_id"], "order_items.order_id contains values not found in orders.order_id"),
        (order_items["product_id"], products["product_id"], "order_items.product_id contains values not found in products.product_id"),
        (payments["order_id"], orders["order_id"], "payments.order_id contains values not found in orders.order_id"),
        (inventory["product_id"], products["product_id"], "inventory.product_id contains values not found in products.product_id"),
        (inventory["store_id"], stores["store_id"], "inventory.store_id contains values not found in stores.store_id"),
    ]
    if not returns.empty:
        checks.extend([
            (returns["order_id"], orders["order_id"], "returns.order_id contains values not found in orders.order_id"),
            (returns["order_item_id"], order_items["order_item_id"], "returns.order_item_id contains values not found in order_items.order_item_id"),
            (returns["product_id"], products["product_id"], "returns.product_id contains values not found in products.product_id"),
        ])
    for child, parent, message in checks:
        child_values = set(child.dropna().astype(str))
        child_values.discard("")
        parent_values = set(parent.dropna().astype(str))
        if child_values - parent_values:
            errors.append(message)


def _check_numeric_rules(frames: dict[str, pd.DataFrame], errors: list[str]) -> None:
    numeric_rules = [
        ("products.csv", "unit_cost", lambda s: s >= 0, "products.unit_cost must be non-negative"),
        ("products.csv", "unit_price", lambda s: s >= 0, "products.unit_price must be non-negative"),
        ("orders.csv", "total_amount", lambda s: s >= 0, "orders.total_amount must be non-negative"),
        ("order_items.csv", "quantity", lambda s: s > 0, "order_items.quantity must be positive"),
        ("order_items.csv", "line_total", lambda s: s >= 0, "order_items.line_total must be non-negative"),
        ("inventory.csv", "quantity_on_hand", lambda s: s >= 0, "inventory.quantity_on_hand must be non-negative"),
        ("returns.csv", "refund_amount", lambda s: s >= 0, "returns.refund_amount must be non-negative"),
    ]
    for filename, column, predicate, message in numeric_rules:
        if filename not in frames or column not in frames[filename].columns or frames[filename].empty:
            continue
        values = pd.to_numeric(frames[filename][column], errors="coerce")
        if values.isna().any() or not predicate(values).all():
            errors.append(message)
    if "products.csv" in frames:
        products = frames["products.csv"]
        if {"unit_price", "unit_cost"}.issubset(products.columns):
            if not (pd.to_numeric(products["unit_price"]) > pd.to_numeric(products["unit_cost"])).all():
                errors.append("products.unit_price must be greater than products.unit_cost")


def validate_source_files(input_dir: str | Path) -> ValidationResult:
    input_path = Path(input_dir)
    errors: list[str] = []
    if not input_path.exists():
        return ValidationResult(False, [f"Input directory does not exist: {input_path}"])
    _check_required_files(input_path, errors)
    frames = _load_frames(input_path, errors)
    if errors:
        return ValidationResult(False, errors)
    _check_relationships(frames, errors)
    _check_numeric_rules(frames, errors)
    return ValidationResult(valid=not errors, errors=errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate retail source CSV files.")
    parser.add_argument("--input-dir", default="data/raw")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = validate_source_files(args.input_dir)
    if result.valid:
        print("Validation passed")
        return
    print("Validation failed")
    for error in result.errors:
        print(f"- {error}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
