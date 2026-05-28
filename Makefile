PROJECT_DIR := $(shell pwd)
AIRFLOW_SERVICE ?= airflow-webserver
AIRFLOW_DAG_ID ?= retail_batch_elt
AIRFLOW_RUN_DATE ?= 2024-01-01
AIRFLOW_TASK_ID ?= dbt_debug
AIRFLOW_RUN_ID ?= manual__$(shell date +%Y%m%dT%H%M%S)
METABASE_SCRIPT := python scripts/provision_metabase.py
WAREHOUSE_QUALITY_SCRIPT := python scripts/warehouse_quality_checks.py
POSTGRES_HOST ?= localhost
POSTGRES_PORT ?= 5432
POSTGRES_DB ?= retail_warehouse
POSTGRES_USER ?= retail_user
POSTGRES_PASSWORD ?= retail_password

.PHONY: up down reset generate-data validate-data load-raw raw-pipeline test quality-check hardening-check apply-indexes verify-indexes warehouse-quality airflow-logs airflow-shell airflow-dags airflow-unpause airflow-trigger airflow-dag-test airflow-task-test airflow-run-local dbt-deps dbt-debug dbt-run dbt-test dbt-snapshot dbt-docs-generate dbt-docs-serve metabase-provision metabase-smoke metabase-reset-note

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

quality-check: test
	@echo "Python tests passed. Run 'make hardening-check' after the local stack has loaded raw and dbt marts."

hardening-check: apply-indexes warehouse-quality

apply-indexes:
	POSTGRES_HOST=$(POSTGRES_HOST) POSTGRES_PORT=$(POSTGRES_PORT) POSTGRES_DB=$(POSTGRES_DB) POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) python scripts/apply_performance_indexes.py

verify-indexes:
	POSTGRES_HOST=$(POSTGRES_HOST) POSTGRES_PORT=$(POSTGRES_PORT) POSTGRES_DB=$(POSTGRES_DB) POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) python -c "import os, psycopg2; conn=psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=int(os.getenv('POSTGRES_PORT')), dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD')); cur=conn.cursor(); cur.execute(\"select count(*) from pg_indexes where schemaname in ('raw', 'marts', 'audit') and indexname like 'idx_%'\"); print(cur.fetchone()[0]); conn.close()"

warehouse-quality:
	$(WAREHOUSE_QUALITY_SCRIPT) --pretty-json

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

dbt-snapshot:
	dbt snapshot $(DBT_FLAGS)

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
