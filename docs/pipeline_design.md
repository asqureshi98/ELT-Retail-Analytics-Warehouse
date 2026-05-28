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
  -> warehouse hardening checks (host/local target)
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

## Warehouse Hardening Checks

Sprint 6 adds an explicit local hardening step after dbt tests. It is not currently embedded in the Airflow DAG; it remains a host/local gate so the existing DAG stays stable while the quality script's container contract is kept simple.

```bash
make hardening-check
```

The target applies idempotent PostgreSQL indexes and runs `scripts/warehouse_quality_checks.py`, which checks mart row counts, revenue sanity, order/item reconciliation, return/refund sanity, duplicate/null keys, audit state, and inventory quantities. The script emits JSON as well as a readable status line.

`make dbt-snapshot` is available for the Sprint 6 customer SCD Type 2 snapshot example. It is optional and separate from the default truncate/reload demo path.

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
- `make hardening-check` exits non-zero when warehouse quality checks fail or PostgreSQL is unavailable.
- Airflow marks the DAG run or task failed when any command exits non-zero.
- Metabase smoke checks exit non-zero when expected assets are missing or representative queries fail.
