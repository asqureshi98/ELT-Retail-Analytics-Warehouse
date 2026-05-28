# Documentation Index

Use this page as the documentation landing page for the completed local retail analytics warehouse.

## Core Documentation

| Document | Purpose |
| --- | --- |
| [Architecture](architecture.md) | Local services, end-to-end ELT flow, schema boundaries, design decisions |
| [Data model](data_model.md) | Source entities, raw tables, dbt layers, dimensions, facts, and quality tests |
| [Pipeline design](pipeline_design.md) | Batch pipeline steps, Airflow DAG, dbt execution, failure behavior |
| [Runbook](runbook.md) | Commands for setup, operation, verification, hardening checks, and troubleshooting |
| [BI dashboard catalog](bi_dashboard_catalog.md) | Metabase dashboards, metrics, cards, representative SQL, provisioning behavior |
| [Hardening roadmap](hardening_roadmap.md) | Sprint 6 quality checks, indexes, SCD2 snapshot example, and future advanced-DE extensions |
| [Portfolio case study](portfolio_case_study.md) | Problem, goals, decisions, outcomes, trade-offs, and roadmap |
| [Project walkthrough](project_walkthrough.md) | Step-by-step evaluator/demo path from clone to shutdown |
| [Sprint status board](kanban_board.md) | Completed sprint scope and definition of done |

## Visual Assets

| Asset | Description |
| --- | --- |
| [Architecture SVG](assets/architecture.svg) | End-to-end local platform diagram |
| [ELT flow SVG](assets/elt_flow.svg) | Operational flow through generation, validation, load, dbt, docs, BI |
| [Dimensional model SVG](assets/dimensional_model.svg) | Marts-layer fact and dimension overview |
| [Asset captions](assets/README.md) | Captions and usage notes for markdown rendering |

## Fast Review Path

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
docker compose config
make quality-check
make up
make airflow-dag-test AIRFLOW_RUN_DATE=2024-01-01
make hardening-check
make metabase-provision
make metabase-smoke
make down
```

If Docker permission is unavailable in the current shell, use:

```bash
sg docker -c 'docker compose config'
sg docker -c 'make up'
```
