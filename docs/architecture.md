# Architecture

## Overview

This project implements a local batch ELT retail analytics warehouse.

## Sprint 1 Architecture

```text
Python Faker Generator
        |
        v
Local CSV Landing Zone: data/raw/
        |
        v
Source Validator
        |
        v
Raw CSV Loader
        |
        v
PostgreSQL raw schema + audit schema
```

## Local Services

Docker Compose runs:

- `postgres`: warehouse database
- `airflow-webserver`: local orchestration UI
- `airflow-scheduler`: DAG scheduler
- `metabase`: dashboard UI

## Schemas

PostgreSQL initializes these schemas:

- `raw`: source-shaped loaded CSV tables
- `staging`: future dbt cleaned models
- `intermediate`: future dbt business logic models
- `marts`: future facts and dimensions
- `audit`: batch and file load metadata

## Sprint 2 Architecture

Sprint 2 extends the pipeline with dbt Core transformations:

```text
Python Faker Generator
        |
        v
Local CSV Landing Zone: data/raw/
        |
        v
Source Validator
        |
        v
Raw CSV Loader
        |
        v
PostgreSQL raw schema + audit schema
        |
        v
dbt Core (Sprint 2)
  staging views (type cleanup)
        |
        v
  intermediate views (business logic)
        |
        v
  marts tables (dimensions + facts)
```

## Design Decisions

- PostgreSQL only for MVP to keep local operation simple.
- Local CSV files are used before adding MinIO/S3 simulation.
- Raw loads use truncate-and-reload for deterministic local development.
- Audit tables track raw file load row counts and batch status.
- Airflow is included in Sprint 1 with a raw pipeline DAG; dbt orchestration comes in Sprint 3.
- dbt staging and intermediate layers are materialised as views to avoid redundant storage.
- dbt mart dimension and fact tables are materialised as tables for query performance.
- The `generate_schema_name` macro overrides the default dbt behaviour so models land in `staging`, `intermediate`, and `marts` rather than prefixed names like `staging_staging`.
