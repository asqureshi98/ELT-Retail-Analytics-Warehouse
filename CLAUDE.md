# Retail Analytics Warehouse

## Project purpose

This repository is a local, production-style batch ELT warehouse for retail analytics. It is designed as a realistic portfolio/data-platform project that runs on a developer machine with Docker Compose and local CSV files.

## Current sprint status

Sprints 1-5 are implemented for the local portfolio scope:

- Sprint 1: Docker Compose foundation, PostgreSQL schemas, synthetic source data generation, source-file validation, raw CSV loading, Airflow raw-pipeline foundation, audit tables, documentation, and pytest coverage.
- Sprint 2: dbt Core modeling for staging, intermediate, and marts layers with tests and documentation generation.
- Sprint 3: Airflow orchestration for the complete local ELT path.
- Sprint 4: Metabase dashboard catalog, API provisioning, and smoke checks.
- Sprint 5: README/docs polish, portfolio case study, evaluator walkthrough, documentation index, lightweight SVG assets, and docs link tests.

## Stack and constraints

- Use PostgreSQL as the only warehouse/database engine.
- Use local CSV storage under `data/raw/` as the host-side landing zone; Airflow DAG runs use `/tmp/retail-analytics-warehouse/raw` inside the container.
- Do not introduce S3, MinIO, cloud storage, or another database unless a task explicitly asks for it.
- Use Docker Compose for local services: PostgreSQL, Airflow, and Metabase.
- Use dbt Core for transformations.
- Use Python scripts for source generation, validation, raw ingestion, and Metabase provisioning.
- Keep the project runnable locally and avoid managed-cloud assumptions.

## Repository map

- `docker-compose.yml` - local PostgreSQL, Airflow, and Metabase services.
- `warehouse/init/` - PostgreSQL schema/table bootstrap SQL.
- `scripts/generate_retail_data.py` - synthetic retail CSV generator.
- `scripts/validate_source_files.py` - source CSV schema/content validator.
- `scripts/load_raw_to_postgres.py` - CSV-to-PostgreSQL raw loader with audit records.
- `scripts/provision_metabase.py` - idempotent Metabase database, collection, card, dashboard provisioning and smoke checks.
- `airflow/dags/retail_batch_elt_dag.py` - Airflow DAG for the full local ELT chain.
- `dbt/retail_warehouse/` - dbt project, profiles, staging/intermediate/marts models, tests, and macros.
- `data/raw/` - local generated source CSV files, ignored when generated.
- `docs/` - architecture, data model, pipeline design, runbook, BI catalog, case study, walkthrough, and assets.
- `tests/` - pytest coverage for generator, validator, Airflow DAG, Metabase provisioning, and docs links/assets.

## Key commands

Run these from the repository root.

```bash
python -m pytest tests -q
docker compose config
make generate-data
make validate-data
```

When Docker is available and services can run locally:

```bash
make up
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make metabase-provision
make metabase-smoke
make down
```

Useful supporting commands:

```bash
make raw-pipeline
make dbt-debug
make dbt-run
make dbt-test
make dbt-docs-generate
make airflow-dags
make airflow-trigger
make airflow-unpause
make airflow-logs
```

## Development guidance

- Prefer small, focused changes that preserve the current local-first architecture.
- For Python or docs-link changes, run `python -m pytest tests -q` before committing.
- For Compose changes, run `docker compose config` before committing.
- For data-contract changes, update tests, docs, dbt models/tests, and validation logic together.
- Keep raw tables source-shaped; put cleanup and business logic in dbt models rather than in raw ingestion.
- Preserve deterministic local development where practical.
- Avoid adding cloud or production-scope claims unless implemented.

## Security and secrets

- Never commit real secrets, passwords, tokens, database dumps, or local `.env` files.
- Treat default local credentials as development-only examples.
- Do not print or persist real credentials in logs, audit rows, docs, tests, or Claude agent files.
