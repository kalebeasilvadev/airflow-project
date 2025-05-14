from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="refresh_view",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 3 * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["kubernetes", "factory", "gitlab"],
) as dag:

    KubernetesPodOperator(
        task_id="run_gitlab_pod",
        namespace="airflow",
        image="grupo/projeto/image-refresh-view:latest",  # Substituir pelo valor real se necessário
        image_pull_secrets=[{"name": "gitlab-registry-secret"}],
        image_pull_policy="Always",
        name="pod-refresh_view",
        labels={"sidecar.istio.io/inject": "false"},
        env_vars={
            "POSTGRES_DB": '{{ var.value.POSTGRES_DB }}',
            "POSTGRES_USER": '{{ var.value.POSTGRES_USER }}',
            "POSTGRES_PASSWORD": '{{ var.value.POSTGRES_PASSWORD }}',
            "POSTGRES_HOST": '{{ var.value.POSTGRES_HOST }}',
            "POSTGRES_PORT": '{{ var.value.POSTGRES_PORT }}',
        },
        resources={
            "request_memory": "512Mi",
            "request_cpu": "500m",
            "limit_memory": "1Gi",
            "limit_cpu": "1000m",
        },
        is_delete_operator_pod=True,
        get_logs=True,
        kube_conn_id="kubernetes_default",
    )
