# Documentation Assets

This directory contains lightweight committed assets used by the README and documentation. They are text-based SVG/Markdown assets so they render on GitHub and do not rely on private local paths.

## Assets

- `architecture.svg` - end-to-end local architecture from CSV generation through Metabase dashboards.
- `elt_flow.svg` - operational ELT sequence used by the pipeline and case-study docs.
- `dimensional_model.svg` - marts-layer fact/dimension overview for the data model.

## Captions

- Architecture overview: "Local Docker Compose platform showing Python ingestion, PostgreSQL warehouse schemas, Airflow orchestration, dbt transformations, and Metabase BI."
- ELT flow: "Batch ELT path from generated source files through validation, audited raw load, dbt model build/test, docs generation, and BI provisioning."
- Dimensional model: "Marts layer with sales, order item, payment, return, and inventory facts connected to customer, product, store, promotion, and date dimensions."
