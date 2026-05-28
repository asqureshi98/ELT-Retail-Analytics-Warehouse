PROJECT_DIR := $(shell pwd)

.PHONY: up down reset generate-data validate-data load-raw raw-pipeline test airflow-logs airflow-shell airflow-dags dbt-deps dbt-debug dbt-run dbt-test dbt-docs-generate dbt-docs-serve

up:
	docker compose up -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d

generate-data:
	python scripts/generate_retail_data.py --orders 10000 --customers 1000 --products 250 --stores 10 --output-dir data/raw

validate-data:
	python scripts/validate_source_files.py --input-dir data/raw

load-raw:
	python scripts/load_raw_to_postgres.py --input-dir data/raw

raw-pipeline: generate-data validate-data load-raw

test:
	python -m pytest tests -q

airflow-logs:
	docker compose logs -f airflow-webserver airflow-scheduler

airflow-shell:
	docker compose exec airflow-webserver bash

airflow-dags:
	docker compose exec airflow-webserver airflow dags list

DBT_FLAGS := --profiles-dir ./dbt/retail_warehouse --project-dir ./dbt/retail_warehouse

dbt-deps:
	dbt deps $(DBT_FLAGS)

dbt-debug:
	dbt debug $(DBT_FLAGS)

dbt-run:
	dbt run $(DBT_FLAGS)

dbt-test:
	dbt test $(DBT_FLAGS)

dbt-docs-generate:
	dbt docs generate $(DBT_FLAGS)

dbt-docs-serve:
	dbt docs serve $(DBT_FLAGS)
