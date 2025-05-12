import os
import yaml
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from datetime import timedelta

DATA_PATH = os.path.join(os.path.dirname(__file__), "data/jobs")


def load_yaml_configs(path):
    jobs = []
    for file in os.listdir(path):
        if file.endswith(".yaml"):
            with open(os.path.join(path, file), "r") as stream:
                try:
                    job = yaml.safe_load(stream)
                    if job.get("enabled", True):
                        jobs.append(job)
                except yaml.YAMLError as e:
                    print(f"❌ Erro ao ler {file}: {e}")
    return jobs


def resolve_airflow_vars(value):
    """Resolve airflow_var no formato airflow_var:VAR_NAME ou embutido na string"""
    if isinstance(value, str):
        if value.startswith("airflow_var:"):
            # Exatamente o valor da variável
            var_name = value.split("airflow_var:")[1]
            return Variable.get(var_name)
        elif "airflow_var:" in value:
            # Substituição embutida
            parts = value.split("airflow_var:")
            resolved = parts[0]
            for part in parts[1:]:
                var_name, rest = (part.split("/", 1) + [""])[:2]
                resolved += Variable.get(var_name) + ("/" + rest if rest else "")
            return resolved
    return value


def deep_resolve(obj):
    """Aplica resolve_airflow_vars recursivamente em dicionários e listas"""
    if isinstance(obj, dict):
        return {k: deep_resolve(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_resolve(item) for item in obj]
    else:
        return resolve_airflow_vars(obj)


def validate_job_config(config):
    required_keys = [
        "dag_id",
        "namespace",
        "image",
        "image_pull_secrets",
        "resources",
        "env_vars",
    ]
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(
            f"❌ Configuração da DAG {config.get('dag_id', 'unknown')} está incompleta: faltam {missing}"
        )


def create_dag(config):
    config = deep_resolve(config)
    validate_job_config(config)

    default_args = {
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    dag = DAG(
        dag_id=config["dag_id"],
        default_args=default_args,
        schedule_interval=config.get("schedule_interval", None),
        start_date=days_ago(1),
        catchup=False,
        tags=["kubernetes", "factory", "gitlab"],
    )

    with dag:
        KubernetesPodOperator(
            task_id="run_gitlab_pod",
            namespace=config["namespace"],
            image=config["image"],
            image_pull_secrets=[{"name": config["image_pull_secrets"]}],
            image_pull_policy="Always",
            name=f"pod-{config['dag_id']}",
            labels={"sidecar.istio.io/inject": "false"},
            env_vars=config["env_vars"],
            resources={
                "request_memory": config["resources"]["request_memory"],
                "request_cpu": config["resources"]["request_cpu"],
                "limit_memory": config["resources"]["limit_memory"],
                "limit_cpu": config["resources"]["limit_cpu"],
            },
            is_delete_operator_pod=True,
            get_logs=True,
            kube_conn_id="kubernetes_default",
        )

    return dag


# 🏭 Factory → cria todas as DAGs dinamicamente
for job_config in load_yaml_configs(DATA_PATH):
    dag_id = job_config["dag_id"]
    globals()[dag_id] = create_dag(job_config)
