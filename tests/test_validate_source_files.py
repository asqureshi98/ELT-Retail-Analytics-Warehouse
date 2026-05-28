import pandas as pd
import pytest

from scripts.generate_retail_data import generate_retail_data
from scripts.validate_source_files import validate_source_files


def test_validate_source_files_passes_for_generated_data(tmp_path):
    generate_retail_data(
        orders=25,
        customers=10,
        products=8,
        stores=2,
        output_dir=tmp_path,
        seed=456,
    )

    result = validate_source_files(tmp_path)

    assert result.valid is True
    assert result.errors == []


def test_validate_source_files_fails_when_required_file_missing(tmp_path):
    generate_retail_data(
        orders=10,
        customers=5,
        products=5,
        stores=2,
        output_dir=tmp_path,
        seed=789,
    )
    (tmp_path / "orders.csv").unlink()

    result = validate_source_files(tmp_path)

    assert result.valid is False
    assert any("Missing required file: orders.csv" in error for error in result.errors)


def test_validate_source_files_fails_on_invalid_foreign_key(tmp_path):
    generate_retail_data(
        orders=10,
        customers=5,
        products=5,
        stores=2,
        output_dir=tmp_path,
        seed=999,
    )
    orders_path = tmp_path / "orders.csv"
    orders = pd.read_csv(orders_path)
    orders.loc[0, "customer_id"] = "missing_customer"
    orders.to_csv(orders_path, index=False)

    result = validate_source_files(tmp_path)

    assert result.valid is False
    assert any("orders.customer_id contains values not found in customers.customer_id" in error for error in result.errors)
