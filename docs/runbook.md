# Runbook

## Start Services

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

The Sprint 1 DAG runs the raw pipeline only. dbt tasks are added in later sprints.

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

### Airflow starts slowly

The MVP compose file installs Python/dbt packages at Airflow container startup. This is acceptable for local Sprint 1, but Sprint 3 should replace it with a custom Airflow image.
