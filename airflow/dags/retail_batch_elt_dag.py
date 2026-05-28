from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

PROJECT_DIR = "/opt/airflow/project"
# Airflow containers run as the `airflow` user, while the repository checkout and
# host-generated `data/raw` directory are owned by the host developer user. Use a
# container-local landing path for DAG runs so Airflow can generate, validate,
# and load batch files without mutating host-owned raw files.
AIRFLOW_DATA_DIR = "/tmp/retail-analytics-warehouse/raw"
DBT_PROJECT_DIR = f"{PROJECT_DIR}/dbt/retail_warehouse"
DBT_PROFILES_DIR = DBT_PROJECT_DIR
DBT_TARGET = "docker"
# Keep dbt runtime artifacts out of the bind-mounted project directory when dbt
# runs as the Airflow container user. Host dbt invocations may own target/logs,
# which would otherwise make Airflow task retries fail with permission errors.
DBT_LOG_PATH = "/tmp/retail-analytics-warehouse/dbt-logs"
DBT_TARGET_PATH = "/tmp/retail-analytics-warehouse/dbt-target"
DBT_ENV = {
    "DBT_PROFILES_DIR": DBT_PROFILES_DIR,
    "DBT_LOG_PATH": DBT_LOG_PATH,
    "DBT_TARGET_PATH": DBT_TARGET_PATH,
    "DBT_POSTGRES_HOST": "postgres",
    "DBT_POSTGRES_PORT": "5432",
    "DBT_POSTGRES_DB": "retail_warehouse",
    "DBT_POSTGRES_USER": "retail_user",
    "DBT_POSTGRES_PASSWORD": "retail_password",
    "DBT_POSTGRES_SCHEMA": "analytics",
}
DBT_FLAGS = (
    f"--project-dir {DBT_PROJECT_DIR} "
    f"--profiles-dir {DBT_PROFILES_DIR} "
    f"--target {DBT_TARGET} "
    f"--log-path {DBT_LOG_PATH}"
)

def dbt_command(subcommand: str) -> str:
    return f"cd {PROJECT_DIR} && dbt {subcommand} {DBT_FLAGS}"


def dbt_operator(task_id: str, subcommand: str) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=dbt_command(subcommand),
        env=DBT_ENV,
        append_env=True,
    )


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
    tags=["retail", "elt", "local", "dbt"],
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
          --output-dir {AIRFLOW_DATA_DIR}
        """,
    )

    validate_source_files = BashOperator(
        task_id="validate_source_files",
        bash_command=f"cd {PROJECT_DIR} && python scripts/validate_source_files.py --input-dir {AIRFLOW_DATA_DIR}",
    )

    load_raw_to_postgres = BashOperator(
        task_id="load_raw_to_postgres",
        bash_command=f"cd {PROJECT_DIR} && python scripts/load_raw_to_postgres.py --input-dir {AIRFLOW_DATA_DIR}",
    )

    dbt_debug = dbt_operator("dbt_debug", "debug --connection")
    dbt_run = dbt_operator("dbt_run", "run")
    dbt_test = dbt_operator("dbt_test", "test")
    dbt_docs_generate = dbt_operator("dbt_docs_generate", "docs generate")

    end = EmptyOperator(task_id="end")

    (
        start
        >> generate_retail_data
        >> validate_source_files
        >> load_raw_to_postgres
        >> dbt_debug
        >> dbt_run
        >> dbt_test
        >> dbt_docs_generate
        >> end
    )
