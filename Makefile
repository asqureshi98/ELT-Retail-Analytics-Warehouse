PROJECT_DIR := $(shell pwd)
AIRFLOW_SERVICE ?= airflow-webserver
AIRFLOW_DAG_ID ?= retail_batch_elt
AIRFLOW_RUN_DATE ?= 2024-01-01
AIRFLOW_TASK_ID ?= dbt_debug
AIRFLOW_RUN_ID ?= manual__$(shell date +%Y%m%dT%H%M%S)
METABASE_SCRIPT := python scripts/provision_metabase.py

.PHONY: up down reset generate-data validate-data load-raw raw-pipeline test airflow-logs airflow-shell airflow-dags airflow-unpause airflow-trigger airflow-dag-test airflow-task-test airflow-run-local dbt-deps dbt-debug dbt-run dbt-test dbt-docs-generate dbt-docs-serve metabase-provision metabase-smoke metabase-reset-note

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
	docker compose exec $(AIRFLOW_SERVICE) airflow dags list

airflow-unpause:
	docker compose exec $(AIRFLOW_SERVICE) airflow dags unpause $(AIRFLOW_DAG_ID)

airflow-trigger:
	docker compose exec $(AIRFLOW_SERVICE) airflow dags trigger $(AIRFLOW_DAG_ID) --run-id $(AIRFLOW_RUN_ID)

airflow-dag-test:
	docker compose exec $(AIRFLOW_SERVICE) airflow dags test $(AIRFLOW_DAG_ID) $(AIRFLOW_RUN_DATE)

airflow-task-test:
	docker compose exec $(AIRFLOW_SERVICE) airflow tasks test $(AIRFLOW_DAG_ID) $(AIRFLOW_TASK_ID) $(AIRFLOW_RUN_DATE)

airflow-run-local: airflow-dag-test

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

metabase-provision:
	$(METABASE_SCRIPT) provision

metabase-smoke:
	$(METABASE_SCRIPT) smoke

metabase-reset-note:
	@echo "Metabase stores local state in the Docker volume metabase_data. Run 'docker compose down -v' or 'make reset' to reset it."
