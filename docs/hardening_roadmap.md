# Sprint 6 Hardening Roadmap

Sprint 6 adds local-first hardening assets that improve observability and reviewer confidence without changing the project into a cloud or streaming platform.

## Implemented in this repository

### Warehouse quality checks

`scripts/warehouse_quality_checks.py` runs post-ELT checks against PostgreSQL and prints both a readable report and a JSON summary. The checks cover:

- Raw and mart row-count presence.
- Revenue non-negativity.
- Raw order subtotal to order-item line-total reconciliation.
- Return/refund references and refund amount sanity.
- Null or duplicate key checks for important raw and mart keys.
- Audit load presence and failed/unfinished audit state.
- Inventory quantity sanity.

Run after the local stack has loaded raw tables and built dbt marts:

```bash
make hardening-check
```

For JSON-only automation:

```bash
python scripts/warehouse_quality_checks.py --json-only --pretty-json
```

The script intentionally stays dependency-light and uses the existing PostgreSQL connection environment variables: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

### Idempotent local indexes

`warehouse/hardening/004_create_performance_indexes.sql` adds `CREATE INDEX IF NOT EXISTS` statements for common raw/marts join keys, date filters, audit status/freshness lookups, and dashboard/quality-check access patterns.

```bash
make apply-indexes
make verify-indexes
```

These indexes are safe to rerun locally. They are kept as an explicit SQL asset rather than hidden in Python so reviewers can inspect the physical-design choices.

### SCD2 snapshot readiness

`dbt/retail_warehouse/snapshots/snap_customers.sql` is a small concrete SCD Type 2 example for customer history using dbt snapshots. It is not part of the default Airflow DAG yet because the local demo path is currently truncate/reload-oriented. Run it explicitly after raw customers exist:

```bash
make dbt-snapshot
```

## Local quality gates

Two Make targets separate always-available checks from database-dependent checks:

```bash
make quality-check     # host pytest; no running services required
make hardening-check   # applies indexes and runs warehouse quality SQL checks; requires PostgreSQL data/marts
```

`make hardening-check` should be run after either:

```bash
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
```

or the host path:

```bash
make raw-pipeline
make dbt-run
make dbt-test
```

## Airflow integration decision

The quality script is documented as a host/local target instead of being added to the Airflow DAG in Sprint 6. This keeps the DAG stable and avoids introducing a second operational concern into the Airflow container before the script has a dedicated container execution contract. A future sprint can add it after `dbt_test` once the container environment, output capture, and failure policy are explicitly designed.

## Future extensions not implemented here

These are credible next steps, but they are intentionally documented rather than claimed as complete:

- Incremental dbt facts: convert append-friendly fact models to incremental materializations with unique keys and late-arriving update handling.
- Broader SCD Type 2 coverage: add product/store snapshots and document snapshot retention/reset procedures for local demos.
- Great Expectations or dbt-expectations: add richer anomaly/expectation checks if dependency weight is acceptable.
- CI workflow: run pytest, docs-link tests, `docker compose config`, SQL linting, and dbt parse in GitHub Actions.
- Data lineage: publish dbt docs artifacts or add OpenLineage-compatible metadata once orchestration is more production-like.
- Cloud migration: map local Postgres/Airflow/Metabase components to managed equivalents, keeping secrets and storage outside the repository.
