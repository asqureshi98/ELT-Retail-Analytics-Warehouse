FROM apache/airflow:2.9.1-python3.11

ARG AIRFLOW_VERSION=2.9.1
ARG PYTHON_VERSION=3.11

COPY airflow/requirements.txt /tmp/airflow-requirements.txt

RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" \
    -r /tmp/airflow-requirements.txt
