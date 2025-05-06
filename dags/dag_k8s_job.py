from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime

with DAG(
    dag_id='test_pod_operator',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['k8s'],
) as dag:

    test_task = KubernetesPodOperator(
        task_id="run_test_pod",
        name="airflow-test",
        namespace="default",
        image="busybox",
        cmds=["sh", "-c", "echo 'Hello from KubernetesPodOperator!'"],
        is_delete_operator_pod=True,
    )
