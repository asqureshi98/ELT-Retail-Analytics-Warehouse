# Pipeline Design

## End-to-End ELT Pipeline

![ELT flow](assets/elt_flow.svg)

```text
generate_retail_data.py
  -> validate_source_files.py
  -> load_raw_to_postgres.py
  -> dbt debug
  -> dbt run
  -> dbt test
  -> dbt docs generate
  -> Metabase provision/smoke checks
```

## Raw Ingestion Steps

1. Generate synthetic retail CSV files in `data/raw/` for host-side runs or `/tmp/retail-analytics-warehouse/raw` inside Airflow containers.
2. Validate required files, required columns, non-empty files, IDs, relationships, and numeric rules.
3. Connect to PostgreSQL using local defaults or environment overrides.
4. Create an `audit.batch_runs` row.
5. Truncate raw tables for deterministic reloads.
6. Load each CSV into its matching `raw` table.
7. Record row counts in `audit.file_loads`.
8. Mark the batch as success or failed.

## dbt Transformation Steps

1. `dbt debug` validates project/profile connectivity.
2. `dbt run` builds staging views, intermediate views, and marts tables.
3. `dbt test` runs source/model tests and the custom order-total business-rule test.
4. `dbt docs generate` creates dbt documentation artifacts.

Host commands use:

```bash
make dbt-debug
make dbt-run
make dbt-test
make dbt-docs-generate
```

## Airflow Orchestration

The `retail_batch_elt` DAG runs the complete local ELT chain:

```text
start -> generate_retail_data -> validate_source_files -> load_raw_to_postgres -> dbt_debug -> dbt_run -> dbt_test -> dbt_docs_generate -> end
```

Useful checks:

```bash
make airflow-dags
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make airflow-task-test AIRFLOW_TASK_ID=dbt_debug AIRFLOW_RUN_DATE=2024-01-01
```

Scheduler-managed run:

```bash
make airflow-unpause
make airflow-trigger
make airflow-logs
```

## Metabase BI Provisioning

Once marts exist, the BI provisioning step creates or updates Metabase assets:

```bash
make metabase-provision
make metabase-smoke
```

`make metabase-smoke` verifies the database connection, collection, dashboards, cards, and representative marts queries.

## Default Local Volume

`make generate-data` uses 10,000 orders by default for fast local validation. Larger portfolio runs can call the generator directly:

```bash
python scripts/generate_retail_data.py \
  --orders 100000 \
  --customers 10000 \
  --products 1000 \
  --stores 25 \
  --output-dir data/raw
```

## Failure Behavior

- Validation exits non-zero when files are missing or invalid.
- Raw loading exits non-zero on database or file load failure.
- Failed loads update audit metadata where possible.
- dbt commands exit non-zero when SQL, source references, relationships, accepted values, or custom business rules fail.
- Airflow marks the DAG run or task failed when any command exits non-zero.
- Metabase smoke checks exit non-zero when expected assets are missing or representative queries fail.
