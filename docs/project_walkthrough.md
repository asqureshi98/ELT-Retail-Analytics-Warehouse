# Project Walkthrough for Evaluators

This walkthrough is designed for a reviewer starting from a fresh clone on a machine with Python, Docker, Docker Compose, and Make available.

## 1. Clone and enter the repository

```bash
git clone <repository-url> retail-analytics-warehouse
cd retail-analytics-warehouse
```

If you are already reviewing the local workspace:

```bash
cd /home/asq/retail-analytics-warehouse
```

## 2. Install host Python dependencies

```bash
python -m pip install -r requirements.txt
```

## 3. Run static/local checks

```bash
python -m pytest tests -q
docker compose config
```

If Docker requires group switching in this shell:

```bash
sg docker -c 'docker compose config'
```

## 4. Start the local services

```bash
make up
```

Services:

- PostgreSQL: `localhost:5432`
- Airflow: <http://localhost:8080> (`admin` / `admin`)
- Metabase: <http://localhost:3000>

## 5. Run the full ELT pipeline through Airflow

```bash
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
```

This executes generation, validation, raw loading, dbt debug/run/test, and dbt docs generation through the `retail_batch_elt` DAG.

## 6. Provision and verify Metabase

```bash
make metabase-provision
make metabase-smoke
```

After provisioning, sign in to Metabase with:

```text
admin@retail-analytics.local / RetailLocalAdmin!2026
```

Open the `Retail Analytics` collection and inspect:

- Executive Sales Overview
- Product and Category Performance
- Store and Channel Performance
- Customer Behavior
- Returns and Refunds
- Inventory Health

## 7. Inspect warehouse results

Use your preferred PostgreSQL client with:

```text
host: localhost
port: 5432
database: retail_warehouse
user: retail_user
password: retail_password
```

Representative SQL:

```sql
select count(*) from raw.orders;
select count(*) from audit.file_loads;
select count(*) from marts.fct_sales;
select count(*) from marts.dim_customers;
select count(*) from marts.fct_inventory_snapshots where needs_restock;
```

## 8. Review the implementation

Suggested files:

- `airflow/dags/retail_batch_elt_dag.py`
- `scripts/generate_retail_data.py`
- `scripts/validate_source_files.py`
- `scripts/load_raw_to_postgres.py`
- `scripts/provision_metabase.py`
- `dbt/retail_warehouse/models/`
- `docs/architecture.md`
- `docs/data_model.md`
- `docs/bi_dashboard_catalog.md`

## 9. Shut down

```bash
make down
```

To delete local Docker volumes and start fresh later:

```bash
make reset
```

`make reset` removes local PostgreSQL and Metabase state because it runs `docker compose down -v` before starting services again.

## Demo Narrative

A concise verbal walkthrough:

1. "This is a local batch ELT warehouse for retail analytics."
2. "Synthetic CSVs stand in for upstream operational extracts."
3. "Python validates and loads source-shaped raw tables with audit metadata."
4. "dbt builds typed staging views, reusable intermediate models, and facts/dimensions in marts."
5. "Airflow orchestrates the complete path in a Docker Compose environment."
6. "Metabase dashboards are provisioned by API, so BI assets are repeatable rather than manually clicked."
7. "The project is intentionally local-only and synthetic; cloud deployment, SCD2, and CI are future roadmap items."
