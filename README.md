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

## Tech Stack

- PostgreSQL 16
- Apache Airflow 2.9.1 Python 3.11 image
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

To start local services:

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
make dbt-debug      # validate dbt profile/project connectivity
make dbt-run        # build staging, intermediate, and marts models
make dbt-test       # run dbt source/model/business-rule tests
make dbt-docs-generate # generate dbt documentation artifacts
```

## Current Status

Sprint 1 and Sprint 2 files are implemented. Later sprints will add full Airflow dbt orchestration and Metabase dashboards.
