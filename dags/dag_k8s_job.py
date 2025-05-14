from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime
import os

from airflow.utils.log.logging_mixin import LoggingMixin

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
log = LoggingMixin().log
log.info(f"Pasta geral {os.path.dirname(__file__)}")
log.info(f"Factory carregado. Arquivos em {DATA_PATH}: {os.listdir(DATA_PATH)}")

with DAG(
    dag_id="test_pod_operator",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["k8s"],
) as dag:
    # Get list of files in DATA_PATH to display in the pod
    files_in_data_path = "\n".join([f"- {f}" for f in os.listdir(DATA_PATH)])

    test_task = KubernetesPodOperator(
        task_id="run_test_pod",
        name="airflow-test",
        namespace="airflow",
        image="busybox",
        cmds=[
            "sh",
            "-c",
            f"echo 'DAG Path: {DATA_PATH}'; echo 'Files in DATA_PATH:'; echo '{files_in_data_path}'; echo 'Hello and wait a bit'; sleep 5",
        ],
        get_logs=True,
        is_delete_operator_pod=True,  # Deleta após capturar logs
    )
