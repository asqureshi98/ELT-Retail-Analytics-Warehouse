# Architecture

## Overview

This project implements a local batch ELT retail analytics warehouse. It is designed as a portfolio-friendly data platform that can be reviewed on a developer machine without cloud services.

![Architecture overview](assets/architecture.svg)

## End-to-End Flow

```text
Python synthetic data generator
  -> local CSV landing zone
  -> source validation
  -> raw PostgreSQL load + audit metadata
  -> dbt staging/intermediate/marts models + tests
  -> Airflow full ELT orchestration
  -> Metabase dashboards provisioned by API
```

## Local Services

Docker Compose runs:

| Service | Purpose | Port |
| --- | --- | --- |
| `postgres` | PostgreSQL 16 warehouse database | `5432` |
| `airflow-webserver` | Airflow UI and CLI target for local checks | `8080` |
| `airflow-scheduler` | Airflow DAG scheduler | internal |
| `metabase` | BI dashboard UI and API | `3000` |

Airflow uses a project image, `retail-airflow:local`, built from `airflow/Dockerfile` and `airflow/requirements.txt`.

## Warehouse Schemas

PostgreSQL initializes these schemas:

- `raw`: source-shaped loaded CSV tables.
- `staging`: dbt views for type cleanup and source normalization.
- `intermediate`: dbt views for reusable business logic.
- `marts`: dbt dimension and fact tables for analytics consumption.
- `audit`: batch and file load metadata.

## Runtime Paths

Host-side commands use:

- CSV landing zone: `data/raw/`.
- dbt project: `dbt/retail_warehouse`.
- dbt profile default host: `localhost`.

Airflow container tasks use:

- Repository mount: `/opt/airflow/project`.
- Writable generated CSV path: `/tmp/retail-analytics-warehouse/raw`.
- dbt project/profile path: `/opt/airflow/project/dbt/retail_warehouse`.
- dbt target: `docker`, which connects to PostgreSQL hostname `postgres`.
- dbt logs/artifacts: `/tmp/retail-analytics-warehouse/dbt-logs` and `/tmp/retail-analytics-warehouse/dbt-target`.

## Layered Architecture

```text
Source layer
  Python Faker generator creates nine CSV files.

Ingestion layer
  validate_source_files.py checks file contracts.
  load_raw_to_postgres.py truncates and reloads raw tables.
  audit.batch_runs and audit.file_loads capture load metadata.

Transformation layer
  dbt staging views cast types and normalize source values.
  dbt intermediate views centralize reusable order and margin logic.
  dbt marts tables expose facts and dimensions for BI.

Orchestration layer
  Airflow DAG retail_batch_elt runs generation, validation, load, dbt debug/run/test, and dbt docs generation.

BI layer
  scripts/provision_metabase.py creates or updates the Metabase database connection, collection, cards, and dashboards.
```

## Design Decisions

- PostgreSQL is the only warehouse engine to keep local setup simple.
- Local CSV files represent upstream extracts without introducing S3/MinIO/cloud dependencies.
- Raw loads use truncate-and-reload for deterministic local demos.
- Raw tables stay source-shaped; business logic is implemented in dbt.
- Staging and intermediate dbt models are views to avoid redundant local storage.
- Mart dimensions and facts are tables for BI query performance.
- The dbt `generate_schema_name` macro prevents duplicated schema prefixes and lands models in `staging`, `intermediate`, and `marts`.
- Airflow runs dbt inside the Docker network with the `docker` dbt target.
- Metabase provisioning is idempotent by asset name to avoid manual dashboard drift.

## Current Completion Status

Sprints 1-5 are implemented for the local portfolio scope: foundation/raw ingestion, dbt marts, Airflow orchestration, Metabase dashboards, and documentation/assets polish.
