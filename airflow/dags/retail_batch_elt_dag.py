from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="retail_batch_elt",
    description="Local batch ELT pipeline for retail analytics warehouse",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["retail", "elt", "local"],
    params={"orders": 10000, "customers": 1000, "products": 250, "stores": 10},
) as dag:
    start = EmptyOperator(task_id="start")

    generate_retail_data = BashOperator(
        task_id="generate_retail_data",
        bash_command=f"""
        set -e
        cd {PROJECT_DIR}
        python scripts/generate_retail_data.py \
          --orders {{{{ params.orders }}}} \
          --customers {{{{ params.customers }}}} \
          --products {{{{ params.products }}}} \
          --stores {{{{ params.stores }}}} \
          --output-dir data/raw
        """,
    )

    validate_source_files = BashOperator(
        task_id="validate_source_files",
        bash_command=f"cd {PROJECT_DIR} && python scripts/validate_source_files.py --input-dir data/raw",
    )

    load_raw_to_postgres = BashOperator(
        task_id="load_raw_to_postgres",
        bash_command=f"cd {PROJECT_DIR} && python scripts/load_raw_to_postgres.py --input-dir data/raw",
    )

    end = EmptyOperator(task_id="end")

    start >> generate_retail_data >> validate_source_files >> load_raw_to_postgres >> end
