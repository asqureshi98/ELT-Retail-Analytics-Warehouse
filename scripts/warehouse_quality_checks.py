#!/usr/bin/env python3
"""Post-ELT warehouse quality checks for the local retail analytics warehouse.

The script runs lightweight SQL checks against PostgreSQL and emits both a
human-readable report and a JSON summary suitable for local automation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Iterable

import psycopg2


@dataclass(frozen=True)
class CheckSpec:
    name: str
    description: str
    sql: str
    metric_key: str
    min_value: float | int | None = None
    max_value: float | int | None = None
    equals: float | int | str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CheckResult:
    name: str
    description: str
    status: str
    passed: bool
    observed_value: Any
    message: str
    details: dict[str, Any]
    tags: tuple[str, ...] = field(default_factory=tuple)


WAREHOUSE_CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec(
        name="raw_orders_non_empty",
        description="raw.orders contains loaded source rows",
        sql="select count(*)::int as row_count from raw.orders",
        metric_key="row_count",
        min_value=1,
        tags=("raw", "row-count"),
    ),
    CheckSpec(
        name="marts_fct_sales_non_empty",
        description="marts.fct_sales contains transformed order facts",
        sql="select count(*)::int as row_count from marts.fct_sales",
        metric_key="row_count",
        min_value=1,
        tags=("marts", "row-count"),
    ),
    CheckSpec(
        name="marts_dimensions_non_empty",
        description="core dimension marts all contain rows",
        sql="""
            select least(
                (select count(*) from marts.dim_customers),
                (select count(*) from marts.dim_products),
                (select count(*) from marts.dim_stores),
                (select count(*) from marts.dim_date)
            )::int as min_dimension_rows
        """,
        metric_key="min_dimension_rows",
        min_value=1,
        tags=("marts", "row-count"),
    ),
    CheckSpec(
        name="revenue_amounts_non_negative",
        description="sales/order item revenue amounts should not be negative",
        sql="""
            select count(*)::int as bad_rows
            from (
                select order_id as key from marts.fct_sales where total_amount < 0 or subtotal_amount < 0
                union all
                select order_item_id as key from marts.fct_order_items where revenue < 0 or line_total < 0
            ) invalid_amounts
        """,
        metric_key="bad_rows",
        equals=0,
        tags=("revenue", "sanity"),
    ),
    CheckSpec(
        name="order_item_line_totals_match_orders",
        description="sum of item gross amounts should reconcile to raw order subtotals within one cent",
        sql="""
            with item_totals as (
                select order_id, round(sum(line_total + discount_amount)::numeric, 2) as item_subtotal
                from raw.order_items
                group by order_id
            )
            select count(*)::int as mismatched_orders
            from raw.orders o
            left join item_totals i on o.order_id = i.order_id
            where i.order_id is null
               or abs(coalesce(i.item_subtotal, 0) - coalesce(o.subtotal_amount, 0)) > 0.01
        """,
        metric_key="mismatched_orders",
        equals=0,
        tags=("orders", "items", "reconciliation"),
    ),
    CheckSpec(
        name="returns_reference_existing_items",
        description="returns must reference existing raw order items and refunds must not exceed line totals",
        sql="""
            select count(*)::int as bad_returns
            from raw.returns r
            left join raw.order_items oi on r.order_item_id = oi.order_item_id
            where oi.order_item_id is null
               or r.refund_amount < 0
               or r.refund_amount > oi.line_total + 0.01
        """,
        metric_key="bad_returns",
        equals=0,
        tags=("returns", "refunds"),
    ),
    CheckSpec(
        name="primary_keys_not_null_or_duplicate",
        description="source-shaped raw keys and mart keys should not be null or duplicated",
        sql="""
            with key_checks as (
                select 'raw.orders.order_id' as key_name, count(*) filter (where order_id is null) as nulls,
                       count(*) - count(distinct order_id) as duplicates from raw.orders
                union all
                select 'raw.order_items.order_item_id', count(*) filter (where order_item_id is null),
                       count(*) - count(distinct order_item_id) from raw.order_items
                union all
                select 'raw.products.product_id', count(*) filter (where product_id is null),
                       count(*) - count(distinct product_id) from raw.products
                union all
                select 'marts.fct_sales.order_id', count(*) filter (where order_id is null),
                       count(*) - count(distinct order_id) from marts.fct_sales
                union all
                select 'marts.fct_order_items.order_item_id', count(*) filter (where order_item_id is null),
                       count(*) - count(distinct order_item_id) from marts.fct_order_items
            )
            select coalesce(sum(nulls + duplicates), 0)::int as bad_keys
            from key_checks
        """,
        metric_key="bad_keys",
        equals=0,
        tags=("keys", "duplicates", "nulls"),
    ),
    CheckSpec(
        name="audit_successful_loads_exist",
        description="audit.file_loads records successful raw loads for source files",
        sql="""
            select count(*)::int as successful_loads
            from audit.file_loads
            where status = 'success' and row_count >= 0
        """,
        metric_key="successful_loads",
        min_value=1,
        tags=("audit", "freshness"),
    ),
    CheckSpec(
        name="audit_no_failed_or_unfinished_batches",
        description="audit tables should not contain failed file loads or unfinished failed batch runs",
        sql="""
            select (
                (select count(*) from audit.file_loads where status <> 'success') +
                (select count(*) from audit.batch_runs where status <> 'success' and finished_at is null)
            )::int as bad_audit_rows
        """,
        metric_key="bad_audit_rows",
        equals=0,
        tags=("audit", "freshness"),
    ),
    CheckSpec(
        name="inventory_quantities_sane",
        description="inventory quantities and reorder levels should be non-negative",
        sql="""
            select count(*)::int as bad_inventory_rows
            from raw.inventory
            where quantity_on_hand < 0 or reorder_level < 0 or restock_quantity < 0
        """,
        metric_key="bad_inventory_rows",
        equals=0,
        tags=("inventory", "sanity"),
    ),
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def evaluate_check(spec: CheckSpec, row: dict[str, Any]) -> CheckResult:
    observed = _json_safe(row.get(spec.metric_key))
    details: dict[str, Any] = {
        "metric_key": spec.metric_key,
        "min_value": spec.min_value,
        "max_value": spec.max_value,
        "equals": spec.equals,
    }

    failures: list[str] = []
    if spec.metric_key not in row:
        failures.append(f"metric '{spec.metric_key}' missing from SQL result")
    elif observed is None:
        failures.append(f"metric '{spec.metric_key}' is null")
    else:
        if spec.equals is not None and observed != spec.equals:
            failures.append(f"expected {spec.metric_key} == {spec.equals}, observed {observed}")
        if spec.min_value is not None and observed < spec.min_value:
            failures.append(f"expected {spec.metric_key} >= {spec.min_value}, observed {observed}")
        if spec.max_value is not None and observed > spec.max_value:
            failures.append(f"expected {spec.metric_key} <= {spec.max_value}, observed {observed}")

    passed = not failures
    return CheckResult(
        name=spec.name,
        description=spec.description,
        status="pass" if passed else "fail",
        passed=passed,
        observed_value=observed,
        message="OK" if passed else "; ".join(failures),
        details=details,
        tags=spec.tags,
    )


def summarize_results(results: Iterable[CheckResult]) -> dict[str, Any]:
    result_list = list(results)
    passed = sum(1 for result in result_list if result.passed)
    failed = len(result_list) - passed
    return {
        "status": "pass" if failed == 0 else "fail",
        "total": len(result_list),
        "passed": passed,
        "failed": failed,
        "exit_code": 0 if failed == 0 else 1,
        "checks": [asdict(result) for result in result_list],
    }


def connect_from_env():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "retail_warehouse"),
        user=os.getenv("POSTGRES_USER", "retail_user"),
        password=os.getenv("POSTGRES_PASSWORD", "retail_password"),
    )


def _fetch_one_dict(cursor) -> dict[str, Any]:
    row = cursor.fetchone()
    if row is None:
        return {}
    return {description.name: value for description, value in zip(cursor.description, row)}


def run_checks(connection, specs: Iterable[CheckSpec] = WAREHOUSE_CHECKS) -> list[CheckResult]:
    results: list[CheckResult] = []
    with connection.cursor() as cursor:
        for spec in specs:
            try:
                cursor.execute(spec.sql)
                results.append(evaluate_check(spec, _fetch_one_dict(cursor)))
            except Exception as exc:  # noqa: BLE001 - each check should report failure and continue.
                connection.rollback()
                results.append(
                    CheckResult(
                        name=spec.name,
                        description=spec.description,
                        status="fail",
                        passed=False,
                        observed_value=None,
                        message=f"SQL execution failed: {exc}",
                        details={"metric_key": spec.metric_key},
                        tags=spec.tags,
                    )
                )
            else:
                connection.rollback()
    return results


def print_human_report(summary: dict[str, Any]) -> None:
    print(f"Warehouse quality checks: {summary['status'].upper()} ({summary['passed']}/{summary['total']} passed)")
    for check in summary["checks"]:
        print(f"[{check['status'].upper()}] {check['name']}: {check['message']} (observed={check['observed_value']})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local retail warehouse quality checks.")
    parser.add_argument("--json-only", action="store_true", help="emit only the JSON summary")
    parser.add_argument("--pretty-json", action="store_true", help="pretty-print JSON summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    with connect_from_env() as connection:
        summary = summarize_results(run_checks(connection))

    if not args.json_only:
        print_human_report(summary)
    print(json.dumps(summary, indent=2 if args.pretty_json else None, default=_json_safe))
    return int(summary["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
