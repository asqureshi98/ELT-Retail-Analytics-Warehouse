import pytest

from scripts.provision_metabase import (
    DASHBOARD_SPECS,
    CARD_SPECS,
    MetabaseConfig,
    build_card_payload,
    build_dashboard_card_payload,
    build_database_payload,
    card_specs_by_name,
    find_by_name,
)


def test_database_payload_uses_compose_postgres_defaults():
    config = MetabaseConfig()

    payload = build_database_payload(config)

    assert payload["engine"] == "postgres"
    assert payload["name"] == "Retail Warehouse"
    assert payload["details"]["host"] == "postgres"
    assert payload["details"]["dbname"] == "retail_warehouse"
    assert payload["details"]["user"] == "retail_user"
    assert payload["details"]["password"] == "retail_password"
    assert payload["auto_run_queries"] is False
    assert payload["is_full_sync"] is True


def test_card_payload_builds_native_question_with_template_tag_free_sql():
    spec = card_specs_by_name()["Executive KPI Summary"]

    payload = build_card_payload(spec, database_id=42, collection_id=7)

    assert payload["name"] == "Executive KPI Summary"
    assert payload["dataset_query"]["database"] == 42
    assert payload["dataset_query"]["type"] == "native"
    assert payload["dataset_query"]["native"]["query"] == spec.sql.strip()
    assert payload["dataset_query"]["native"]["template-tags"] == {}
    assert payload["collection_id"] == 7
    assert payload["display"] in {"table", "scalar", "bar", "line", "row"}
    assert payload["visualization_settings"]["provisioned_by"] == "retail-analytics-warehouse"


def test_dashboard_specs_cover_required_sprint4_catalog_areas():
    dashboard_names = {dashboard.name for dashboard in DASHBOARD_SPECS}
    expected = {
        "Executive Sales Overview",
        "Product and Category Performance",
        "Store and Channel Performance",
        "Customer Behavior",
        "Returns and Refunds",
        "Inventory Health",
    }

    assert expected.issubset(dashboard_names)
    assert len(CARD_SPECS) >= 12


def test_build_dashboard_card_payload_is_deterministic_grid():
    payload = build_dashboard_card_payload(card_id=10, dashboard_id=20, row=2, col=3, size_x=8, size_y=5)

    assert payload == {
        "cardId": 10,
        "dashboardId": 20,
        "row": 2,
        "col": 3,
        "sizeX": 8,
        "sizeY": 5,
        "parameter_mappings": [],
        "visualization_settings": {},
    }


def test_find_by_name_is_case_insensitive_and_returns_none_for_missing():
    items = [{"id": 1, "name": "Retail Analytics"}, {"id": 2, "name": "Executive Sales Overview"}]

    assert find_by_name(items, "retail analytics")["id"] == 1
    assert find_by_name(items, "EXECUTIVE SALES OVERVIEW")["id"] == 2
    assert find_by_name(items, "missing") is None


def test_card_names_are_unique_and_assigned_to_existing_dashboards():
    names = [spec.name for spec in CARD_SPECS]
    dashboards = {dashboard.name for dashboard in DASHBOARD_SPECS}

    assert len(names) == len(set(names))
    assert all(spec.dashboard_name in dashboards for spec in CARD_SPECS)
