# Project Sprint Status

This document summarizes completed implementation scope for the local retail analytics warehouse.

## Done

### Sprint 1: Local foundation and raw ingestion

- Docker Compose stack for PostgreSQL, Airflow, and Metabase.
- PostgreSQL schemas: `raw`, `staging`, `intermediate`, `marts`, `audit`.
- Raw source tables for synthetic retail CSV data.
- Synthetic retail data generator.
- Source file validator.
- Raw CSV loader with batch/file audit records.
- Makefile developer commands.
- Pytest coverage for generator and validator behavior.

### Sprint 2: dbt warehouse models

- dbt project under `dbt/retail_warehouse`.
- Raw source definitions and staging models for every raw table.
- Intermediate sales/order item business logic models.
- Marts dimensions and facts in the `marts` schema.
- dbt schema tests and custom order-total business-rule test.

### Sprint 3: Airflow full ELT orchestration

- `retail_batch_elt` DAG for generation, validation, raw load, dbt debug/run/test, and dbt docs generation.
- Container-safe dbt profile/project execution against the Docker Compose `postgres` service.
- Make targets for listing, testing, triggering, and unpausing the DAG.

### Sprint 4: Metabase BI dashboards

- Dashboard and metric catalog in `docs/bi_dashboard_catalog.md`.
- Idempotent Metabase API provisioning in `scripts/provision_metabase.py`.
- `Retail Analytics` collection with executive, product/category, store/channel, customer, returns/refunds, and inventory health dashboards.
- Make targets for provisioning and API smoke verification.

### Sprint 5: Documentation polish and portfolio assets

- README rewritten as a portfolio overview and quickstart.
- Documentation landing page, case study, evaluator walkthrough, and visual assets.
- Existing architecture, data model, pipeline, runbook, and BI docs aligned to current scope.
- Documentation link/asset validation added to pytest.

## Definition of Done

- Project runs locally through Docker Compose.
- Python tests pass with `python -m pytest tests -q`.
- Docker Compose configuration validates with `docker compose config`.
- The Airflow DAG can run the complete ELT path through `make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01` when services are running.
- Metabase assets can be provisioned and smoke-checked with `make metabase-provision` and `make metabase-smoke` after marts exist.
- README and docs present an honest local-only portfolio package without claiming production/cloud scope.
