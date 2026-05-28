# Retail Analytics Warehouse

A local, production-style batch ELT warehouse for retail analytics using Docker Compose, PostgreSQL, Airflow, Python, and Metabase.

## Sprint Scope

Sprint 1 implements the local foundation and raw ingestion pipeline:

- Docker Compose services for PostgreSQL, Airflow, and Metabase
- PostgreSQL schemas: `raw`, `staging`, `intermediate`, `marts`, `audit`
- Raw source tables for retail CSV data
- Synthetic retail data generator
- Source file validator
- Raw CSV loader with audit records
- Makefile developer commands
- Pytest coverage for generator and validator behavior

Sprint 2 adds dbt Core warehouse modeling:

- dbt project under `dbt/retail_warehouse`
- raw source definitions and staging models for every raw table
- intermediate sales/order item business logic models
- marts dimensions and facts in the `marts` schema
- dbt schema tests plus a custom order-total business-rule test

Sprint 3 adds Airflow orchestration for the complete local ELT path:

- Airflow DAG chain: generate source CSVs in a container-local writable landing path, validate files, load raw tables, run `dbt debug`, `dbt run`, `dbt test`, and generate dbt docs
- Container-safe dbt execution from `/opt/airflow/project/dbt/retail_warehouse` against the Docker Compose `postgres` service
- Headless Make targets for listing, testing, triggering, and unpausing the Airflow DAG

## Tech Stack

- PostgreSQL 16
- Apache Airflow 2.9.1 Python 3.11 image with isolated Airflow runtime dependencies
- Metabase latest
- Python, pandas, Faker, psycopg2
- dbt Core with the dbt-postgres adapter
- Docker Compose

## Quick Start

```bash
cd /home/asq/retail-analytics-warehouse
cp .env.example .env
python -m pip install -r requirements.txt
make test
make generate-data
make validate-data
```

To start local services (builds the project Airflow image with dependencies from `airflow/requirements.txt`):

```bash
make up
```

To load raw CSV files after PostgreSQL is running:

```bash
make load-raw
```

Or run the full raw pipeline:

```bash
make raw-pipeline
```

To build and test the Sprint 2 dbt warehouse models after raw data is loaded:

```bash
make dbt-debug
make dbt-run
make dbt-test
```

To run the Sprint 3 full Airflow ELT orchestration after services are up:

```bash
make airflow-dags
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
```

For a scheduler-managed run instead of a one-shot local DAG test:

```bash
make airflow-unpause
make airflow-trigger
make airflow-logs
```

## Local UIs

- Airflow: <http://localhost:8080>
- Metabase: <http://localhost:3000>
- PostgreSQL: `localhost:5432`

Default Airflow user created by the compose init task:

```text
username: admin
password: admin
```

## Data Files

Generated CSVs are written to:

```text
data/raw/
```

Expected files:

```text
customers.csv
products.csv
stores.csv
promotions.csv
orders.csv
order_items.csv
payments.csv
inventory.csv
returns.csv
```

## Useful Commands

```bash
make up             # start Docker services
make down           # stop services
make reset          # reset Docker volumes and restart
make generate-data  # generate 10k synthetic orders by default
make validate-data  # validate source CSVs
make load-raw       # load CSVs to PostgreSQL raw schema
make raw-pipeline   # generate, validate, and load
make test           # run pytest tests
make airflow-dags   # list Airflow DAGs from the container
make airflow-dag-test # run retail_batch_elt once with airflow dags test
make airflow-task-test AIRFLOW_TASK_ID=dbt_run # test one task headlessly
make airflow-trigger # trigger a scheduler-managed DAG run
make airflow-unpause # unpause the retail_batch_elt DAG
make dbt-debug      # validate dbt profile/project connectivity
make dbt-run        # build staging, intermediate, and marts models
make dbt-test       # run dbt source/model/business-rule tests
make dbt-docs-generate # generate dbt documentation artifacts
```

## Full Airflow ELT DAG

The `retail_batch_elt` DAG now orchestrates the full Sprint 3 chain:

```text
start -> generate_retail_data -> validate_source_files -> load_raw_to_postgres -> dbt_debug -> dbt_run -> dbt_test -> dbt_docs_generate -> end
```

Inside Airflow containers, generated CSVs land in `/tmp/retail-analytics-warehouse/raw` so DAG runs do not need write access to the host-owned `data/raw` directory. dbt runs with `DBT_PROFILES_DIR=/opt/airflow/project/dbt/retail_warehouse`, `--project-dir /opt/airflow/project/dbt/retail_warehouse`, `--profiles-dir /opt/airflow/project/dbt/retail_warehouse`, and `--target docker` so the profile connects to the Docker Compose `postgres` hostname. Airflow dbt tasks also send dbt logs and compiled artifacts to `/tmp/retail-analytics-warehouse/dbt-logs` and `/tmp/retail-analytics-warehouse/dbt-target` to avoid host/container ownership conflicts in the bind-mounted project tree.

## Current Status

Sprint 1, Sprint 2, and Sprint 3 files are implemented. Later sprints will add Metabase dashboards and any production hardening beyond the local Docker Compose workflow.
