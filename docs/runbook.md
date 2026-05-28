# Runbook

## Prerequisites

- Python with `pip`.
- Docker and Docker Compose.
- Make.
- Access to the Docker daemon. In this Hermes shell, Docker commands may require `sg docker -c '<command>'`.

Install host dependencies:

```bash
python -m pip install -r requirements.txt
```

## Start Services

`make up` builds the local `retail-airflow:local` image from `airflow/Dockerfile`. Airflow installs only `airflow/requirements.txt` under Apache Airflow constraints, keeping container dependencies isolated from host/dev `requirements.txt`.

```bash
make up
```

## Stop Services

```bash
make down
```

## Reset Environment

```bash
make reset
```

`make reset` runs `docker compose down -v` and then starts services again. This deletes local PostgreSQL and Metabase Docker volume state.

## Generate Source Data

```bash
make generate-data
```

## Validate Source Data

```bash
make validate-data
```

## Load Raw Tables

```bash
make load-raw
```

## Run Full Raw Pipeline

```bash
make raw-pipeline
```

## Run Tests

```bash
python -m pytest tests -q
```

Equivalent Make target:

```bash
make test
```

## Validate Docker Compose

```bash
docker compose config
```

If Docker permissions require group switching:

```bash
sg docker -c 'docker compose config'
```

## Run dbt Warehouse Models

Start/load PostgreSQL first:

```bash
make up
make raw-pipeline
```

Then validate, build, and test dbt models from the repository root:

```bash
make dbt-debug
make dbt-run
make dbt-test
```

The committed `dbt/retail_warehouse/profiles.yml` uses local development defaults and can be overridden with `DBT_POSTGRES_HOST`, `DBT_POSTGRES_PORT`, `DBT_POSTGRES_DB`, `DBT_POSTGRES_USER`, `DBT_POSTGRES_PASSWORD`, and `DBT_POSTGRES_SCHEMA`. Use target `docker` from inside Docker-networked contexts if needed:

```bash
dbt run --profiles-dir ./dbt/retail_warehouse --project-dir ./dbt/retail_warehouse --target docker
```

## Verify PostgreSQL Data

After a raw load or full DAG run, connect to PostgreSQL and run:

```sql
select count(*) from raw.orders;
select count(*) from raw.order_items;
select * from audit.batch_runs order by started_at desc limit 1;
select * from audit.file_loads order by loaded_at desc limit 9;
select count(*) from marts.fct_sales;
select count(*) from marts.dim_customers;
```

## Sprint 6 Hardening Checks

After raw tables and dbt marts exist, run the local hardening gate:

```bash
make hardening-check
```

This target applies idempotent indexes from `warehouse/hardening/004_create_performance_indexes.sql` and runs `scripts/warehouse_quality_checks.py`. The quality script prints a human-readable status line plus JSON details for local automation. It checks row-count presence, revenue sanity, order-item reconciliation, return/refund sanity, duplicate/null key conditions, audit load state, and inventory quantity sanity.

Useful standalone commands:

```bash
make apply-indexes
make verify-indexes
make warehouse-quality
python scripts/warehouse_quality_checks.py --json-only --pretty-json
```

Connection overrides use the same local PostgreSQL variables as other host tools: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Inside Docker-networked contexts use `POSTGRES_HOST=postgres`; from the host use `POSTGRES_HOST=localhost`.

`make quality-check` is the service-free gate for pytest. It does not require PostgreSQL to be running:

```bash
make quality-check
```

## dbt Customer Snapshot Example

Sprint 6 includes a small SCD Type 2 readiness example in `dbt/retail_warehouse/snapshots/snap_customers.sql`. It is intentionally not part of the default Airflow DAG yet. Run it explicitly after raw customers exist:

```bash
make dbt-snapshot
```

See [hardening_roadmap.md](hardening_roadmap.md) for implemented hardening scope and future extensions.

## Airflow

Open:

```text
http://localhost:8080
```

Default local credentials:

```text
admin / admin
```

The `retail_batch_elt` DAG runs the full local ELT path:

```text
start -> generate_retail_data -> validate_source_files -> load_raw_to_postgres -> dbt_debug -> dbt_run -> dbt_test -> dbt_docs_generate -> end
```

Airflow mounts the repository at `/opt/airflow/project`. DAG runs use `/tmp/retail-analytics-warehouse/raw` as the container-local writable landing path for generated CSV files. The dbt tasks run with `DBT_PROFILES_DIR=/opt/airflow/project/dbt/retail_warehouse`, `--project-dir /opt/airflow/project/dbt/retail_warehouse`, `--profiles-dir /opt/airflow/project/dbt/retail_warehouse`, and `--target docker`, which uses the Docker-network `postgres` hostname. dbt logs and compiled artifacts are written under `/tmp/retail-analytics-warehouse/dbt-logs` and `/tmp/retail-analytics-warehouse/dbt-target` inside the container.

Headless Airflow checks and runs:

```bash
make airflow-dags
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make airflow-task-test AIRFLOW_TASK_ID=dbt_debug AIRFLOW_RUN_DATE=2024-01-01
```

Use the scheduler for a normal manual run:

```bash
make airflow-unpause
make airflow-trigger
make airflow-logs
```

If this shell cannot access Docker directly, wrap service commands with the Docker group helper:

```bash
sg docker -c 'make up'
sg docker -c 'make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01'
sg docker -c 'docker compose down'
```

Expected success checks after a full DAG run:

```sql
select count(*) from raw.orders;
select count(*) from audit.file_loads;
select count(*) from marts.fct_sales;
select count(*) from marts.dim_customers;
```

## Metabase

Open:

```text
http://localhost:3000
```

Sprint 4 provisions Metabase through the HTTP API. On first run, `make metabase-provision` completes local setup with development credentials, connects Metabase to PostgreSQL, creates the `Retail Analytics` collection, creates native SQL questions, and places them on dashboards.

Default local Metabase credentials:

```text
email: admin@retail-analytics.local
password: RetailLocalAdmin!2026
```

Provision and verify after the full ELT path has built dbt marts:

```bash
make up
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make metabase-provision
make metabase-smoke
```

Equivalent non-Airflow data path:

```bash
make raw-pipeline
make dbt-run
make dbt-test
make metabase-provision
make metabase-smoke
```

Expected Metabase assets:

- Database: `Retail Warehouse`
- Collection: `Retail Analytics`
- Dashboards: `Executive Sales Overview`, `Product and Category Performance`, `Store and Channel Performance`, `Customer Behavior`, `Returns and Refunds`, `Inventory Health`
- Cards include `Executive KPI Summary`, `Daily Net Sales Trend`, `Category Revenue and Margin`, `Top Products by Revenue`, `Store Channel Sales`, `Customer Lifetime Value Leaders`, `Return Rate Summary`, `Restock Risk by Store`, and `Low Stock Products`

The provisioning script is idempotent by asset name. Reruns update existing database/card/dashboard metadata and add missing dashboard-card links instead of creating unbounded duplicates. Metabase connects to PostgreSQL from inside Docker using host `postgres`. Host scripts call Metabase at `http://localhost:3000`.

Useful environment overrides:

```text
METABASE_URL=http://localhost:3000
METABASE_EMAIL=admin@retail-analytics.local
METABASE_PASSWORD=RetailLocalAdmin!2026
METABASE_POSTGRES_HOST=postgres
METABASE_POSTGRES_PORT=5432
METABASE_POSTGRES_DB=retail_warehouse
METABASE_POSTGRES_USER=retail_user
METABASE_POSTGRES_PASSWORD=retail_password
```

Representative marts checks run by `make metabase-smoke` through Metabase:

```sql
select count(*) as row_count from marts.fct_sales;
select count(*) as row_count from marts.fct_order_items;
select count(*) as row_count from marts.dim_customers;
```

To reset Metabase local state, run `make metabase-reset-note` for the reminder or reset Docker volumes with `docker compose down -v` / `make reset`. This deletes the local Metabase application database and requires provisioning again.

## Portfolio Demo Path

For a clean demo, follow [project_walkthrough.md](project_walkthrough.md): test, validate Compose, run the Airflow DAG, provision Metabase, smoke-check BI, inspect dashboards, and shut down.

## Troubleshooting

### PostgreSQL connection fails

```bash
docker compose ps
```

From host machine use `POSTGRES_HOST=localhost`. Inside Docker use `POSTGRES_HOST=postgres`.

### Validation fails

Run:

```bash
python scripts/validate_source_files.py --input-dir data/raw
```

Read the listed missing file, missing column, relationship, or numeric-rule error.

### Airflow DAG import or dbt task fails

Check the container can see the DAG and dbt installation:

```bash
make airflow-dags
docker compose exec airflow-webserver dbt --version
```

If dbt cannot connect from an Airflow task, confirm the task is using target `docker` and the `postgres` service hostname, not `localhost`.

### Metabase provisioning fails

Confirm services are running and Metabase is reachable:

```bash
docker compose ps
curl -fsS http://localhost:3000/api/session/properties
```

If login fails after a previous local setup, either export `METABASE_EMAIL` and `METABASE_PASSWORD` for the existing local admin account or reset the local Metabase volume with `docker compose down -v` / `make reset` and rerun `make metabase-provision`.

If Metabase cannot connect to PostgreSQL, keep `METABASE_POSTGRES_HOST=postgres`; `localhost` is only correct for host-side PostgreSQL clients, not for Metabase running inside Docker Compose.

If `make metabase-smoke` reports representative queries returning zero rows, run the full ELT path first (`make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01` or `make raw-pipeline && make dbt-run && make dbt-test`).

### Airflow dependency conflicts

Airflow uses a dedicated Docker image built from `airflow/Dockerfile` and `airflow/requirements.txt`. Do not install the top-level `requirements.txt` in Airflow containers; it is for host/dev tooling and can pin versions that conflict with Apache Airflow constraints.
