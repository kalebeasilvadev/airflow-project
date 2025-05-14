from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime
import os

dag_file_path = os.path.abspath(__file__)

with DAG(
    dag_id="test_pod_operator",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["k8s"],
) as dag:
    test_task = KubernetesPodOperator(
        task_id="run_test_pod",
        name="airflow-test",
        namespace="airflow",
        image="busybox",
        cmds=["sh", "-c", f"echo 'DAG Path: {dag_file_path}'; echo 'Hello and wait a bit'; sleep 5"],
        get_logs=True,
        is_delete_operator_pod=True,  # Deleta após capturar logs
    )
