# Retail Analytics Warehouse

A local-first batch ELT project that turns synthetic retail data into a tested PostgreSQL analytics warehouse, orchestrated by Airflow and visualized in Metabase.

This repository is designed as a public, portfolio-ready data engineering project. It demonstrates practical warehouse patterns—source validation, audited raw ingestion, dbt transformations, automated orchestration, quality checks, and BI provisioning—without requiring cloud accounts or managed services.

```text
Synthetic retail CSVs -> PostgreSQL raw schema -> dbt models -> Airflow ELT DAG -> Metabase dashboards
```

![Architecture overview](docs/assets/architecture.svg)

## Highlights

- Deterministic retail data generation for customers, products, stores, promotions, orders, payments, inventory, and returns.
- Source file validation before loading data into the warehouse.
- Audited raw ingestion into PostgreSQL with repeatable local reloads.
- dbt staging, intermediate, dimension, and fact models for analytics-ready marts.
- dbt tests for keys, relationships, accepted values, and business rules.
- Airflow DAG for the full ELT path: generate, validate, load, transform, test, and document.
- Metabase dashboard provisioning through code, including smoke checks.
- Warehouse hardening utilities for quality checks, performance indexes, and a customer snapshot example.
- Pytest coverage for scripts, orchestration structure, BI definitions, quality logic, and documentation links.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Runtime | Docker Compose |
| Warehouse | PostgreSQL 16 |
| Orchestration | Apache Airflow 2.9.1 |
| Transformations | dbt Core + dbt-postgres |
| BI | Metabase |
| Scripts | Python, pandas, Faker, psycopg2 |
| Quality | pytest, dbt tests, custom warehouse checks |

## Repository Structure

```text
.
├── airflow/                  # Airflow image, requirements, and retail_batch_elt DAG
├── dbt/retail_warehouse/     # dbt project with staging, intermediate, marts, and snapshots
├── docs/                     # Architecture, data model, runbook, dashboard catalog, roadmap
├── scripts/                  # Data generation, validation, loading, quality, and BI provisioning
├── tests/                    # Python and documentation tests
├── warehouse/                # PostgreSQL initialization and performance index SQL
├── docker-compose.yml        # Local PostgreSQL, Airflow, and Metabase services
├── Makefile                  # Common local commands
└── README.md
```

Full documentation starts at [docs/index.md](docs/index.md).

## Data Model

The marts layer contains:

- Dimensions: `dim_customers`, `dim_products`, `dim_stores`, `dim_promotions`, `dim_date`
- Facts: `fct_sales`, `fct_order_items`, `fct_payments`, `fct_returns`, `fct_inventory_snapshots`

![Dimensional model overview](docs/assets/dimensional_model.svg)

See [docs/data_model.md](docs/data_model.md) for table grains, relationships, and test coverage.

## Analytics Dashboards

Metabase provisioning creates a `Retail Analytics` collection with dashboards for:

| Dashboard | Focus |
| --- | --- |
| Executive Sales Overview | Net sales, refunds, average order value, payment health, daily trend |
| Product and Category Performance | Revenue, units sold, margin, top products |
| Store and Channel Performance | Store/channel sales and average order value |
| Customer Behavior | Geography and customer lifetime sales |
| Returns and Refunds | Return rates, refund exposure, return reasons |
| Inventory Health | Restock risk by store and product |

Metric definitions and representative SQL are documented in [docs/bi_dashboard_catalog.md](docs/bi_dashboard_catalog.md).

## Quickstart

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- GNU Make

Install Python dependencies and run the fast checks:

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
docker compose config
```

Start the local stack:

```bash
make up
```

Run the full Airflow ELT flow:

```bash
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
```

Provision and verify Metabase dashboards after the marts are built:

```bash
make metabase-provision
make metabase-smoke
```

Run warehouse hardening checks:

```bash
make hardening-check
```

Shut down local services:

```bash
make down
```

## Useful Commands

| Command | Purpose |
| --- | --- |
| `make up` | Start PostgreSQL, Airflow, and Metabase |
| `make down` | Stop local services |
| `make reset` | Recreate local Docker volumes and services |
| `make raw-pipeline` | Generate, validate, and load raw retail data |
| `make dbt-run` | Build dbt models |
| `make dbt-test` | Run dbt tests |
| `make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01` | Execute the ELT DAG locally |
| `make metabase-provision` | Create/update Metabase dashboards through the API |
| `make metabase-smoke` | Verify provisioned dashboard assets |
| `make hardening-check` | Apply indexes and run warehouse quality checks |
| `make dbt-snapshot` | Run the customer snapshot example |

## Local Service URLs

| Service | URL |
| --- | --- |
| Airflow | <http://localhost:8080> |
| Metabase | <http://localhost:3000> |
| PostgreSQL | `localhost:5432` |

Default local development credentials are defined in `docker-compose.yml` and provisioning scripts. They are intentionally for local use only.

## Verification Checklist

Before sharing or reviewing the project, run:

```bash
python -m pytest tests -q
docker compose config
make up
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make hardening-check
make metabase-provision
make metabase-smoke
make down
```

## Documentation

- [Architecture](docs/architecture.md)
- [Data model](docs/data_model.md)
- [Pipeline design](docs/pipeline_design.md)
- [Runbook](docs/runbook.md)
- [BI dashboard catalog](docs/bi_dashboard_catalog.md)
- [Hardening roadmap](docs/hardening_roadmap.md)
- [Portfolio case study](docs/portfolio_case_study.md)
- [Project walkthrough](docs/project_walkthrough.md)

## Scope and Limitations

This is a local analytics warehouse project built with synthetic data and development credentials. It is not a production deployment. The project does not include cloud infrastructure, production CI/CD, streaming ingestion, high availability, autoscaling, or production secrets management.

Future extensions are documented in [docs/hardening_roadmap.md](docs/hardening_roadmap.md), including broader incremental modeling, additional SCD Type 2 coverage, Great Expectations, lineage, and cloud migration paths.

## License

Add a license before distributing or reusing this project outside your own portfolio.
