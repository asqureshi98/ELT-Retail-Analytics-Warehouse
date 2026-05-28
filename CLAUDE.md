# Retail Analytics Warehouse

## Project purpose

This repository is a local, production-style batch ELT warehouse for retail analytics. It is designed as a realistic portfolio/data-platform project that runs on a developer machine with Docker Compose and local CSV files.

## Current sprint status

- Sprint 1 is implemented.
- Sprint 1 includes the Docker Compose foundation, PostgreSQL schemas, synthetic source data generation, source-file validation, raw CSV loading, Airflow raw-pipeline DAG, audit tables, documentation, and pytest coverage for data generation/validation.
- Sprint 2 will add dbt Core modeling for staging, intermediate, and marts layers.
- Later work may expand Airflow orchestration for dbt and add Metabase dashboards.

## Stack and constraints

- Use PostgreSQL as the only warehouse/database engine.
- Use local CSV storage under `data/raw/` as the landing zone; do not introduce S3, MinIO, cloud storage, or another database unless a task explicitly asks for it.
- Use Docker Compose for local services: PostgreSQL, Airflow, and Metabase.
- Use dbt Core for transformations when Sprint 2 modeling is added.
- Use Python scripts for source generation, validation, and raw ingestion.
- Keep the project runnable locally and avoid managed-cloud assumptions.

## Repository map

- `docker-compose.yml` - local PostgreSQL, Airflow, and Metabase services.
- `warehouse/init/` - PostgreSQL schema/table bootstrap SQL.
- `scripts/generate_retail_data.py` - synthetic retail CSV generator.
- `scripts/validate_source_files.py` - source CSV schema/content validator.
- `scripts/load_raw_to_postgres.py` - CSV-to-PostgreSQL raw loader with audit records.
- `airflow/dags/retail_batch_elt_dag.py` - Airflow DAG for the raw pipeline.
- `data/raw/` - local generated source CSV files.
- `docs/` - architecture, data model, pipeline design, runbook, and kanban notes.
- `tests/` - pytest coverage for generator and validator behavior.

## Key commands

Run these from the repository root.

```bash
make test
make generate-data
make validate-data
docker compose config
```

When Docker is available and services can run locally:

```bash
make raw-pipeline
```

Useful supporting commands:

```bash
make up
make down
make reset
make load-raw
make airflow-logs
make airflow-dags
```

## Development guidance

- Prefer small, focused changes that preserve the current local-first architecture.
- For Python changes, run `python -m pytest tests -q` before committing.
- For Compose changes, run `docker compose config` before committing.
- For data-contract changes, update tests, docs, and validation logic together.
- Keep raw tables source-shaped; put cleanup and business logic in future dbt models rather than in raw ingestion.
- Preserve deterministic local development where practical.

## Security and secrets

- Never commit real secrets, passwords, tokens, database dumps, or local `.env` files.
- Commit only `.env.example` for environment documentation.
- Treat default local credentials as development-only examples.
- Do not print or persist credentials in logs, audit rows, docs, tests, or Claude agent files.

## Claude Code project agents

Project-level Claude subagents live in `.claude/agents/`:

- `data-platform-architect` - architecture decisions, warehouse layering, orchestration boundaries, and local-first platform design.
- `retail-dbt-engineer` - Sprint 2 dbt Core models, tests, sources, docs, and warehouse semantics.
- `qa-reviewer` - verification, regression risk, test coverage, Docker Compose checks, and release-readiness review.
