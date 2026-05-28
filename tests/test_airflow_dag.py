from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


class FakeDAG:
    current = None

    def __init__(self, dag_id: str, **kwargs):
        self.dag_id = dag_id
        self.kwargs = kwargs
        self.task_dict = {}

    def __enter__(self):
        FakeDAG.current = self
        return self

    def __exit__(self, exc_type, exc, tb):
        FakeDAG.current = None

    @property
    def tasks(self):
        return list(self.task_dict.values())


class FakeOperator:
    def __init__(self, task_id: str, **kwargs):
        self.task_id = task_id
        self.kwargs = kwargs
        self.downstream_task_ids = set()
        self.upstream_task_ids = set()
        if FakeDAG.current is not None:
            FakeDAG.current.task_dict[task_id] = self

    def __rshift__(self, other):
        self.downstream_task_ids.add(other.task_id)
        other.upstream_task_ids.add(self.task_id)
        return other


class FakeBashOperator(FakeOperator):
    @property
    def bash_command(self):
        return self.kwargs["bash_command"]

    @property
    def env(self):
        return self.kwargs.get("env", {})


def install_fake_airflow(monkeypatch):
    airflow_module = types.ModuleType("airflow")
    setattr(airflow_module, "DAG", FakeDAG)

    operators_module = types.ModuleType("airflow.operators")
    bash_module = types.ModuleType("airflow.operators.bash")
    empty_module = types.ModuleType("airflow.operators.empty")
    setattr(bash_module, "BashOperator", FakeBashOperator)
    setattr(empty_module, "EmptyOperator", FakeOperator)

    monkeypatch.setitem(sys.modules, "airflow", airflow_module)
    monkeypatch.setitem(sys.modules, "airflow.operators", operators_module)
    monkeypatch.setitem(sys.modules, "airflow.operators.bash", bash_module)
    monkeypatch.setitem(sys.modules, "airflow.operators.empty", empty_module)


def load_dag_module(monkeypatch):
    install_fake_airflow(monkeypatch)
    dag_path = Path(__file__).resolve().parents[1] / "airflow" / "dags" / "retail_batch_elt_dag.py"
    spec = importlib.util.spec_from_file_location("retail_batch_elt_dag_under_test", dag_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retail_batch_elt_dag_has_full_sprint_3_task_chain(monkeypatch):
    module = load_dag_module(monkeypatch)
    dag = module.dag

    expected_chain = [
        "start",
        "generate_retail_data",
        "validate_source_files",
        "load_raw_to_postgres",
        "dbt_debug",
        "dbt_run",
        "dbt_test",
        "dbt_docs_generate",
        "end",
    ]

    assert dag.dag_id == "retail_batch_elt"
    assert set(dag.task_dict) == set(expected_chain)
    for upstream, downstream in zip(expected_chain, expected_chain[1:]):
        assert downstream in dag.task_dict[upstream].downstream_task_ids
        assert upstream in dag.task_dict[downstream].upstream_task_ids


def test_airflow_raw_tasks_use_container_writable_landing_path(monkeypatch):
    module = load_dag_module(monkeypatch)
    dag = module.dag

    assert module.AIRFLOW_DATA_DIR == "/tmp/retail-analytics-warehouse/raw"
    assert "--output-dir /tmp/retail-analytics-warehouse/raw" in dag.task_dict[
        "generate_retail_data"
    ].bash_command
    assert "--input-dir /tmp/retail-analytics-warehouse/raw" in dag.task_dict[
        "validate_source_files"
    ].bash_command
    assert "--input-dir /tmp/retail-analytics-warehouse/raw" in dag.task_dict[
        "load_raw_to_postgres"
    ].bash_command


def test_dbt_tasks_use_container_project_paths_and_docker_target(monkeypatch):
    module = load_dag_module(monkeypatch)
    dag = module.dag

    for task_id, subcommand in {
        "dbt_debug": "dbt debug",
        "dbt_run": "dbt run",
        "dbt_test": "dbt test",
        "dbt_docs_generate": "dbt docs generate",
    }.items():
        task = dag.task_dict[task_id]
        assert subcommand in task.bash_command
        if task_id == "dbt_debug":
            assert "--connection" in task.bash_command
        assert "--project-dir /opt/airflow/project/dbt/retail_warehouse" in task.bash_command
        assert "--profiles-dir /opt/airflow/project/dbt/retail_warehouse" in task.bash_command
        assert "--target docker" in task.bash_command
        assert "--log-path /tmp/retail-analytics-warehouse/dbt-logs" in task.bash_command
        assert task.env["DBT_PROFILES_DIR"] == "/opt/airflow/project/dbt/retail_warehouse"
        assert task.env["DBT_POSTGRES_HOST"] == "postgres"
        assert task.env["DBT_LOG_PATH"] == "/tmp/retail-analytics-warehouse/dbt-logs"
        assert task.env["DBT_TARGET_PATH"] == "/tmp/retail-analytics-warehouse/dbt-target"
