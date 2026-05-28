# Pipeline Design

## Sprint 1 Raw Pipeline

```text
generate_retail_data.py
  -> validate_source_files.py
  -> load_raw_to_postgres.py
  -> audit.batch_runs + audit.file_loads
```

## Sprint 2 dbt Transformation Pipeline

```text
raw PostgreSQL tables
  -> dbt staging views
  -> dbt intermediate views
  -> dbt marts dimension/fact tables
  -> dbt data tests and custom business-rule tests
```

dbt is intentionally manual in Sprint 2. Airflow continues to orchestrate only the raw pipeline until a later sprint wires dbt into the DAG.

## Steps

1. Generate synthetic retail CSV files in `data/raw/`.
2. Validate required files, required columns, non-empty files, IDs, relationships, and numeric rules.
3. Connect to PostgreSQL using `.env` values.
4. Create an `audit.batch_runs` row.
5. Truncate raw tables for deterministic reloads.
6. Load each CSV into its matching `raw` table.
7. Record row counts in `audit.file_loads`.
8. Mark the batch as success or failed.

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
- dbt parse/build/test exits non-zero when SQL, source references, relationships, accepted values, or custom business rules fail.
