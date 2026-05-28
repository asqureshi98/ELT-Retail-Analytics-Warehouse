# Runbook

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
make test
```

## Run dbt Warehouse Models

Install Python dependencies and start/load PostgreSQL first:

```bash
python -m pip install -r requirements.txt
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

After `make up` and `make load-raw`, connect to PostgreSQL and run:

```sql
select count(*) from raw.orders;
select count(*) from raw.order_items;
select * from audit.batch_runs order by started_at desc limit 1;
select * from audit.file_loads order by loaded_at desc limit 9;
```

## Airflow

Open:

```text
http://localhost:8080
```

Default local credentials:

```text
admin / admin
```

The Sprint 1 DAG runs the raw pipeline only. Sprint 2 dbt models are run manually with Makefile commands; Airflow dbt tasks are added in later sprints.

## Metabase

Open:

```text
http://localhost:3000
```

Connect to PostgreSQL from inside Docker using host `postgres`.

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

### Airflow dependency conflicts

Airflow uses a dedicated Docker image built from `airflow/Dockerfile` and `airflow/requirements.txt`. Do not install the top-level `requirements.txt` in Airflow containers; it is for host/dev tooling and can pin versions that conflict with Apache Airflow constraints.
