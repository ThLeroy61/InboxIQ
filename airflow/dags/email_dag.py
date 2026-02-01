from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 9),
    'retries': 1,
}

with DAG(
    dag_id='app_email_dag',
    default_args=default_args,
    schedule_interval='0 */3 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['TriMail'],
) as dag:

    run_app_script = BashOperator(
        task_id='run_app_script',
        bash_command='cd /opt/email_ingestion && python -m email_pipeline.app'
    )

    run_clean_script = BashOperator(
        task_id='run_clean_script',
        bash_command='cd /opt/email_ingestion && python -m email_pipeline.clean'
    )
    
    run_app_script >> run_clean_script