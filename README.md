# Retail Analytics Warehouse

A local, production-style batch ELT warehouse for retail analytics using Docker Compose, PostgreSQL, Airflow, Python, and Metabase.

## Sprint 1 Scope

Sprint 1 implements the local foundation and raw ingestion pipeline:

- Docker Compose services for PostgreSQL, Airflow, and Metabase
- PostgreSQL schemas: `raw`, `staging`, `intermediate`, `marts`, `audit`
- Raw source tables for retail CSV data
- Synthetic retail data generator
- Source file validator
- Raw CSV loader with audit records
- Makefile developer commands
- Pytest coverage for generator and validator behavior

## Tech Stack

- PostgreSQL 16
- Apache Airflow 2.9.1 Python 3.11 image
- Metabase latest
- Python, pandas, Faker, psycopg2
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
```

## Current Status

Sprint 1 files are implemented. Later sprints will add dbt staging/intermediate/marts models, full Airflow dbt orchestration, and Metabase dashboards.
