#!/usr/bin/env python3
"""Provision local Metabase assets for the retail analytics warehouse.

The script intentionally uses only the Python standard library so it can run in a
fresh local development checkout after `python -m pip install -r requirements.txt`.
It is safe to rerun: collections, cards, dashboards, and the warehouse database
connection are looked up by name before create/update calls are made.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable


PROVISIONED_BY = "retail-analytics-warehouse"
DEFAULT_COLLECTION_NAME = "Retail Analytics"
DEFAULT_DATABASE_NAME = "Retail Warehouse"
DEFAULT_ADMIN_EMAIL = "admin@retail-analytics.local"
DEFAULT_ADMIN_PASSWORD = "RetailLocalAdmin!2026"
DEFAULT_ADMIN_FIRST_NAME = "Retail"
DEFAULT_ADMIN_LAST_NAME = "Admin"


@dataclass(frozen=True)
class MetabaseConfig:
    """Runtime configuration for host-to-Metabase and Metabase-to-Postgres calls."""

    url: str = field(default_factory=lambda: os.getenv("METABASE_URL", "http://localhost:3000"))
    email: str = field(default_factory=lambda: os.getenv("METABASE_EMAIL", DEFAULT_ADMIN_EMAIL))
    password: str = field(default_factory=lambda: os.getenv("METABASE_PASSWORD", DEFAULT_ADMIN_PASSWORD))
    first_name: str = field(default_factory=lambda: os.getenv("METABASE_FIRST_NAME", DEFAULT_ADMIN_FIRST_NAME))
    last_name: str = field(default_factory=lambda: os.getenv("METABASE_LAST_NAME", DEFAULT_ADMIN_LAST_NAME))
    collection_name: str = field(default_factory=lambda: os.getenv("METABASE_COLLECTION_NAME", DEFAULT_COLLECTION_NAME))
    database_name: str = field(default_factory=lambda: os.getenv("METABASE_DATABASE_NAME", DEFAULT_DATABASE_NAME))
    postgres_host: str = field(default_factory=lambda: os.getenv("METABASE_POSTGRES_HOST", "postgres"))
    postgres_port: int = field(default_factory=lambda: int(os.getenv("METABASE_POSTGRES_PORT", "5432")))
    postgres_db: str = field(default_factory=lambda: os.getenv("METABASE_POSTGRES_DB", "retail_warehouse"))
    postgres_user: str = field(default_factory=lambda: os.getenv("METABASE_POSTGRES_USER", "retail_user"))
    postgres_password: str = field(default_factory=lambda: os.getenv("METABASE_POSTGRES_PASSWORD", "retail_password"))
    wait_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("METABASE_WAIT_TIMEOUT_SECONDS", "180")))

    @property
    def base_url(self) -> str:
        return self.url.rstrip("/")


@dataclass(frozen=True)
class DashboardSpec:
    name: str
    description: str


@dataclass(frozen=True)
class CardSpec:
    name: str
    description: str
    dashboard_name: str
    sql: str
    display: str = "table"
    row: int = 0
    col: int = 0
    size_x: int = 12
    size_y: int = 4
    visualization_settings: dict[str, Any] = field(default_factory=dict)


DASHBOARD_SPECS: tuple[DashboardSpec, ...] = (
    DashboardSpec("Executive Sales Overview", "Revenue, orders, AOV, payment status, and sales trend KPIs for leadership."),
    DashboardSpec("Product and Category Performance", "Category, product, brand, and gross margin performance views."),
    DashboardSpec("Store and Channel Performance", "Store and channel revenue, order, and margin comparisons."),
    DashboardSpec("Customer Behavior", "Customer geography, repeat purchasing, and lifetime value views."),
    DashboardSpec("Returns and Refunds", "Return rate, refund exposure, return reasons, and product return hot spots."),
    DashboardSpec("Inventory Health", "Stock-on-hand, reorder, and restock risk views by product and store."),
)


CARD_SPECS: tuple[CardSpec, ...] = (
    CardSpec(
        name="Executive KPI Summary",
        description="Top-line orders, paid revenue, discounts, refunds, and average order value.",
        dashboard_name="Executive Sales Overview",
        display="table",
        row=0,
        col=0,
        size_x=24,
        size_y=4,
        sql="""
select
    count(*) as orders,
    count(*) filter (where is_paid) as paid_orders,
    round(sum(total_amount)::numeric, 2) as gross_sales,
    round(sum(discount_amount)::numeric, 2) as discounts,
    round(sum(total_refund_amount)::numeric, 2) as refunds,
    round((sum(total_amount) - sum(total_refund_amount))::numeric, 2) as net_sales,
    round(avg(total_amount)::numeric, 2) as average_order_value
from marts.fct_sales;
""",
    ),
    CardSpec(
        name="Daily Net Sales Trend",
        description="Daily gross, refund, and net sales trend.",
        dashboard_name="Executive Sales Overview",
        display="line",
        row=4,
        col=0,
        size_x=24,
        size_y=7,
        sql="""
select
    order_date_day,
    round(sum(total_amount)::numeric, 2) as gross_sales,
    round(sum(total_refund_amount)::numeric, 2) as refunds,
    round((sum(total_amount) - sum(total_refund_amount))::numeric, 2) as net_sales,
    count(*) as orders
from marts.fct_sales
group by order_date_day
order by order_date_day;
""",
    ),
    CardSpec(
        name="Payment Status Mix",
        description="Orders and revenue by payment status.",
        dashboard_name="Executive Sales Overview",
        display="bar",
        row=11,
        col=0,
        size_x=12,
        size_y=6,
        sql="""
select
    payment_status,
    count(*) as orders,
    round(sum(total_amount)::numeric, 2) as gross_sales
from marts.fct_sales
group by payment_status
order by gross_sales desc;
""",
    ),
    CardSpec(
        name="Category Revenue and Margin",
        description="Revenue, gross profit, and margin by product category.",
        dashboard_name="Product and Category Performance",
        display="bar",
        row=0,
        col=0,
        size_x=24,
        size_y=7,
        sql="""
select
    category,
    round(sum(revenue)::numeric, 2) as revenue,
    round(sum(gross_profit)::numeric, 2) as gross_profit,
    round((sum(gross_profit) / nullif(sum(revenue), 0))::numeric, 4) as gross_margin_pct,
    sum(quantity) as units_sold
from marts.fct_order_items
group by category
order by revenue desc;
""",
    ),
    CardSpec(
        name="Top Products by Revenue",
        description="Highest revenue products with quantity and margin context.",
        dashboard_name="Product and Category Performance",
        display="table",
        row=7,
        col=0,
        size_x=24,
        size_y=8,
        sql="""
select
    product_name,
    category,
    brand,
    sum(quantity) as units_sold,
    round(sum(revenue)::numeric, 2) as revenue,
    round(sum(gross_profit)::numeric, 2) as gross_profit,
    round((sum(gross_profit) / nullif(sum(revenue), 0))::numeric, 4) as gross_margin_pct
from marts.fct_order_items
group by product_name, category, brand
order by revenue desc
limit 15;
""",
    ),
    CardSpec(
        name="Store Channel Sales",
        description="Revenue, orders, and AOV by retail channel.",
        dashboard_name="Store and Channel Performance",
        display="bar",
        row=0,
        col=0,
        size_x=12,
        size_y=6,
        sql="""
select
    s.channel,
    count(*) as orders,
    round(sum(f.total_amount)::numeric, 2) as gross_sales,
    round(avg(f.total_amount)::numeric, 2) as average_order_value
from marts.fct_sales f
join marts.dim_stores s on f.store_id = s.store_id
group by s.channel
order by gross_sales desc;
""",
    ),
    CardSpec(
        name="Top Stores by Net Sales",
        description="Store leaderboard after refunds.",
        dashboard_name="Store and Channel Performance",
        display="table",
        row=0,
        col=12,
        size_x=12,
        size_y=8,
        sql="""
select
    s.store_name,
    s.channel,
    s.city,
    s.state,
    count(*) as orders,
    round((sum(f.total_amount) - sum(f.total_refund_amount))::numeric, 2) as net_sales
from marts.fct_sales f
join marts.dim_stores s on f.store_id = s.store_id
group by s.store_name, s.channel, s.city, s.state
order by net_sales desc
limit 15;
""",
    ),
    CardSpec(
        name="Customer Geography",
        description="Customer base by state.",
        dashboard_name="Customer Behavior",
        display="bar",
        row=0,
        col=0,
        size_x=12,
        size_y=6,
        sql="""
select
    state,
    count(*) as customers
from marts.dim_customers
group by state
order by customers desc
limit 15;
""",
    ),
    CardSpec(
        name="Customer Lifetime Value Leaders",
        description="Highest value customers based on net sales.",
        dashboard_name="Customer Behavior",
        display="table",
        row=0,
        col=12,
        size_x=12,
        size_y=8,
        sql="""
select
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    c.city,
    c.state,
    count(f.order_id) as orders,
    round((sum(f.total_amount) - sum(f.total_refund_amount))::numeric, 2) as lifetime_net_sales
from marts.fct_sales f
join marts.dim_customers c on f.customer_id = c.customer_id
group by c.customer_id, customer_name, c.city, c.state
order by lifetime_net_sales desc
limit 15;
""",
    ),
    CardSpec(
        name="Return Rate Summary",
        description="Return rate and refund amount by order cohort day.",
        dashboard_name="Returns and Refunds",
        display="line",
        row=0,
        col=0,
        size_x=24,
        size_y=7,
        sql="""
select
    order_date_day,
    count(*) as orders,
    count(*) filter (where has_return) as returned_orders,
    round((count(*) filter (where has_return)::numeric / nullif(count(*), 0)), 4) as return_rate,
    round(sum(total_refund_amount)::numeric, 2) as refund_amount
from marts.fct_sales
group by order_date_day
order by order_date_day;
""",
    ),
    CardSpec(
        name="Refunds by Return Reason",
        description="Return reason counts and refund exposure.",
        dashboard_name="Returns and Refunds",
        display="bar",
        row=7,
        col=0,
        size_x=12,
        size_y=6,
        sql="""
select
    return_reason,
    count(*) as returns,
    round(sum(refund_amount)::numeric, 2) as refund_amount
from marts.fct_returns
group by return_reason
order by refund_amount desc;
""",
    ),
    CardSpec(
        name="Restock Risk by Store",
        description="Products at or below reorder level by store.",
        dashboard_name="Inventory Health",
        display="table",
        row=0,
        col=0,
        size_x=12,
        size_y=7,
        sql="""
select
    s.store_name,
    s.channel,
    count(*) filter (where i.needs_restock) as products_needing_restock,
    sum(i.quantity_on_hand) as units_on_hand,
    sum(i.restock_quantity) filter (where i.needs_restock) as suggested_restock_units
from marts.fct_inventory_snapshots i
join marts.dim_stores s on i.store_id = s.store_id
group by s.store_name, s.channel
order by products_needing_restock desc, suggested_restock_units desc;
""",
    ),
    CardSpec(
        name="Low Stock Products",
        description="Product/store inventory rows at or below reorder threshold.",
        dashboard_name="Inventory Health",
        display="table",
        row=0,
        col=12,
        size_x=12,
        size_y=8,
        sql="""
select
    p.product_name,
    p.category,
    s.store_name,
    i.quantity_on_hand,
    i.reorder_level,
    i.restock_quantity
from marts.fct_inventory_snapshots i
join marts.dim_products p on i.product_id = p.product_id
join marts.dim_stores s on i.store_id = s.store_id
where i.needs_restock
order by i.quantity_on_hand asc, i.restock_quantity desc
limit 25;
""",
    ),
)


SMOKE_SQL: tuple[str, ...] = (
    "select count(*) as row_count from marts.fct_sales;",
    "select count(*) as row_count from marts.fct_order_items;",
    "select count(*) as row_count from marts.dim_customers;",
)


def card_specs_by_name() -> dict[str, CardSpec]:
    return {spec.name: spec for spec in CARD_SPECS}


def find_by_name(items: Iterable[dict[str, Any]], name: str) -> dict[str, Any] | None:
    wanted = name.casefold()
    for item in items:
        if str(item.get("name", "")).casefold() == wanted:
            return item
    return None


def build_database_payload(config: MetabaseConfig) -> dict[str, Any]:
    return {
        "name": config.database_name,
        "engine": "postgres",
        "details": {
            "host": config.postgres_host,
            "port": config.postgres_port,
            "dbname": config.postgres_db,
            "user": config.postgres_user,
            "password": config.postgres_password,
            "ssl": False,
            "tunnel-enabled": False,
        },
        "auto_run_queries": False,
        "is_full_sync": True,
        "is_on_demand": False,
        "schedules": {},
    }


def build_card_payload(spec: CardSpec, database_id: int, collection_id: int) -> dict[str, Any]:
    visualization_settings = {"provisioned_by": PROVISIONED_BY}
    visualization_settings.update(spec.visualization_settings)
    return {
        "name": spec.name,
        "description": spec.description,
        "display": spec.display,
        "dataset_query": {
            "database": database_id,
            "type": "native",
            "native": {"query": spec.sql.strip(), "template-tags": {}},
        },
        "visualization_settings": visualization_settings,
        "collection_id": collection_id,
    }


def build_dashboard_card_payload(
    card_id: int,
    dashboard_id: int,
    row: int,
    col: int,
    size_x: int,
    size_y: int,
) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "dashboardId": dashboard_id,
        "row": row,
        "col": col,
        "sizeX": size_x,
        "sizeY": size_y,
        "parameter_mappings": [],
        "visualization_settings": {},
    }


class MetabaseClient:
    def __init__(self, config: MetabaseConfig):
        self.config = config
        self.session_id: str | None = None

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None, auth: bool = True) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if auth and self.session_id:
            headers["X-Metabase-Session"] = self.session_id
        req = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
                if not body:
                    return None
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Metabase API {method} {path} failed with HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Metabase API {method} {path} failed: {exc.reason}") from exc

    def wait_until_ready(self) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.wait_timeout_seconds
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                props = self.request("GET", "/api/session/properties", auth=False)
                if isinstance(props, dict):
                    return props
            except Exception as exc:  # noqa: BLE001 - waiting tolerates transient startup failures.
                last_error = exc
            time.sleep(3)
        raise TimeoutError(f"Metabase did not become ready within {self.config.wait_timeout_seconds}s: {last_error}")

    def setup_or_login(self) -> None:
        props = self.wait_until_ready()
        setup_token = props.get("setup-token")
        if setup_token:
            payload = {
                "token": setup_token,
                "user": {
                    "email": self.config.email,
                    "password": self.config.password,
                    "first_name": self.config.first_name,
                    "last_name": self.config.last_name,
                },
                "prefs": {"site_name": "Retail Analytics Warehouse", "site_locale": "en"},
            }
            try:
                result = self.request("POST", "/api/setup", payload, auth=False)
                self.session_id = result.get("id") if isinstance(result, dict) else None
            except RuntimeError as exc:
                # Recent Metabase builds may keep returning a setup token briefly even
                # after the first user has been created. Fall back to normal login.
                if "can only be used to create the first user" not in str(exc):
                    raise
        if not self.session_id:
            result = self.request("POST", "/api/session", {"username": self.config.email, "password": self.config.password}, auth=False)
            self.session_id = result["id"]

    def list_databases(self) -> list[dict[str, Any]]:
        result = self.request("GET", "/api/database")
        if isinstance(result, dict):
            return result.get("data", [])
        return result or []

    def list_collections(self) -> list[dict[str, Any]]:
        result = self.request("GET", "/api/collection")
        if isinstance(result, dict):
            return result.get("data", [])
        return result or []

    def list_cards(self) -> list[dict[str, Any]]:
        result = self.request("GET", "/api/card")
        if isinstance(result, dict):
            return result.get("data", result.get("models", []))
        return result or []

    def list_dashboards(self) -> list[dict[str, Any]]:
        result = self.request("GET", "/api/dashboard")
        if isinstance(result, dict):
            return result.get("data", [])
        return result or []

    def ensure_database(self) -> int:
        existing = find_by_name(self.list_databases(), self.config.database_name)
        if existing:
            database_id = int(existing["id"])
            self.request("PUT", f"/api/database/{database_id}", build_database_payload(self.config))
        else:
            created = self.request("POST", "/api/database", build_database_payload(self.config))
            database_id = int(created["id"])
        try:
            self.request("POST", f"/api/database/{database_id}/sync_schema", {})
        except RuntimeError as exc:
            print(f"warning: schema sync request failed; continuing: {exc}", file=sys.stderr)
        return database_id

    def ensure_collection(self) -> int:
        existing = find_by_name(self.list_collections(), self.config.collection_name)
        if existing:
            return int(existing["id"])
        created = self.request(
            "POST",
            "/api/collection",
            {"name": self.config.collection_name, "description": "Provisioned local BI assets for the retail analytics warehouse."},
        )
        return int(created["id"])

    def ensure_dashboard(self, spec: DashboardSpec, collection_id: int) -> int:
        existing = find_by_name(self.list_dashboards(), spec.name)
        payload = {"name": spec.name, "description": spec.description, "collection_id": collection_id}
        if existing:
            dashboard_id = int(existing["id"])
            self.request("PUT", f"/api/dashboard/{dashboard_id}", payload)
            return dashboard_id
        created = self.request("POST", "/api/dashboard", payload)
        return int(created["id"])

    def ensure_card(self, spec: CardSpec, database_id: int, collection_id: int) -> int:
        existing = find_by_name(self.list_cards(), spec.name)
        payload = build_card_payload(spec, database_id=database_id, collection_id=collection_id)
        if existing:
            card_id = int(existing["id"])
            self.request("PUT", f"/api/card/{card_id}", payload)
            return card_id
        created = self.request("POST", "/api/card", payload)
        return int(created["id"])

    def get_dashboard(self, dashboard_id: int) -> dict[str, Any]:
        return self.request("GET", f"/api/dashboard/{dashboard_id}")

    def ensure_dashboard_card(self, dashboard_id: int, card_id: int, spec: CardSpec) -> None:
        dashboard = self.get_dashboard(dashboard_id)
        dashcards = dashboard.get("dashcards") or dashboard.get("ordered_cards") or []
        if any(int(item.get("card_id") or item.get("card", {}).get("id") or -1) == card_id for item in dashcards):
            return
        new_dashcard = {
            "id": -1,
            "card_id": card_id,
            "row": spec.row,
            "col": spec.col,
            "size_x": spec.size_x,
            "size_y": spec.size_y,
            "parameter_mappings": [],
            "visualization_settings": {},
        }
        updated_dashcards = [
            {
                "id": item.get("id"),
                "card_id": item.get("card_id") or item.get("card", {}).get("id"),
                "row": item.get("row", 0),
                "col": item.get("col", 0),
                "size_x": item.get("size_x", item.get("sizeX", 12)),
                "size_y": item.get("size_y", item.get("sizeY", 4)),
                "parameter_mappings": item.get("parameter_mappings") or [],
                "visualization_settings": item.get("visualization_settings") or {},
            }
            for item in dashcards
        ]
        updated_dashcards.append(new_dashcard)
        self.request(
            "PUT",
            f"/api/dashboard/{dashboard_id}",
            {
                "name": dashboard["name"],
                "description": dashboard.get("description"),
                "collection_id": dashboard.get("collection_id"),
                "dashcards": updated_dashcards,
            },
        )

    def run_native_query(self, database_id: int, sql: str) -> int:
        payload = {"database": database_id, "type": "native", "native": {"query": sql, "template-tags": {}}}
        result = self.request("POST", "/api/dataset", payload)
        rows = result.get("data", {}).get("rows", []) if isinstance(result, dict) else []
        if not rows:
            return 0
        first = rows[0]
        try:
            return int(first[0])
        except (TypeError, ValueError, IndexError):
            return len(rows)


def provision(config: MetabaseConfig) -> dict[str, Any]:
    client = MetabaseClient(config)
    client.setup_or_login()
    database_id = client.ensure_database()
    collection_id = client.ensure_collection()
    dashboard_ids = {spec.name: client.ensure_dashboard(spec, collection_id) for spec in DASHBOARD_SPECS}
    card_ids: dict[str, int] = {}
    for spec in CARD_SPECS:
        card_id = client.ensure_card(spec, database_id, collection_id)
        card_ids[spec.name] = card_id
        client.ensure_dashboard_card(dashboard_ids[spec.dashboard_name], card_id, spec)
    return {"database_id": database_id, "collection_id": collection_id, "dashboards": dashboard_ids, "cards": card_ids}


def smoke(config: MetabaseConfig) -> dict[str, Any]:
    client = MetabaseClient(config)
    client.setup_or_login()
    database = find_by_name(client.list_databases(), config.database_name)
    collection = find_by_name(client.list_collections(), config.collection_name)
    cards = client.list_cards()
    dashboards = client.list_dashboards()
    missing_cards = [spec.name for spec in CARD_SPECS if find_by_name(cards, spec.name) is None]
    missing_dashboards = [spec.name for spec in DASHBOARD_SPECS if find_by_name(dashboards, spec.name) is None]
    errors: list[str] = []
    if database is None:
        errors.append(f"missing database: {config.database_name}")
    if collection is None:
        errors.append(f"missing collection: {config.collection_name}")
    errors.extend(f"missing card: {name}" for name in missing_cards)
    errors.extend(f"missing dashboard: {name}" for name in missing_dashboards)

    query_counts: dict[str, int] = {}
    if database is not None:
        database_id = int(database["id"])
        for sql in SMOKE_SQL:
            count = client.run_native_query(database_id, sql)
            query_counts[sql] = count
            if count <= 0:
                errors.append(f"representative query returned no rows: {sql}")

    if errors:
        raise RuntimeError("Metabase smoke check failed:\n- " + "\n- ".join(errors))
    assert database is not None
    assert collection is not None
    return {
        "database": database["name"],
        "collection": collection["name"],
        "dashboards": len(DASHBOARD_SPECS),
        "cards": len(CARD_SPECS),
        "query_counts": query_counts,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("provision", "smoke"), help="Provision assets or verify expected assets and data.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = MetabaseConfig()
    if args.command == "provision":
        result = provision(config)
    else:
        result = smoke(config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
