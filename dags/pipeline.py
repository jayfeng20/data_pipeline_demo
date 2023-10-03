import airflow
from airflow.decorators import task
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.amazon.aws.operators.sns import SnsPublishOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.models import Connection
from airflow.models.baseoperator import chain
import pyspark
import datetime
import logging
import sys


# sys.path.append("${AIRFLOW_HOME}/lib")
# import dag_helper

# {{ ds }} = the execution date of the running DAG
# {{ prev_ds }} = the previous execution date of the running DAG
# {{ next_ds }} = the next executin date of the running DAG
# {{ dag }} = the currrent dag project
# {{ params }} = data accessible from your operators
# {{ var.value.key_of_my_var }} = access variables stored in the metadatabase
# {{ task_instance.xcom_pull() }} = get variables from other tasks

# reports are automatically generated every 5 minutes during workdays
reporter = DAG(
    dag_id="Reporter",
    description="Manages log and config analysis workflow",
    schedule="1 * * * 0,1,2,3,4",
    start_date=datetime.datetime.now(),
    default_args={
        "retries": 2,
        "owner": "Jonathan",
        "email_on_failure": True,
        "email_on_retry": True,
        # "email": ["jonathanfeng2001@gmail.com"],
    },
    catchup=False,
)

# scan and load files from google drive
google_drive_logs = "${AIRFLOW_HOME}/data/sample_log_folders/filename"
google_drive_confs = "${AIRFLOW_HOME}/data/sample_log_folders/filename"


################################################
# HELPER FUNCTIONS
def get_xcom(write_to, key, **kwargs):
    ti = kwargs["ti"]
    content = ti.xcom_pull(task_ids=f"{key}")
    write_to = content


################################################

# spark tasks' configurations
# spark_conf = {
#     "conf": {
#         "spark.yarn.maxAppAttempts": "1",
#         "spark.yarn.executor.memoryOverhead": "512",
#     },
#     "conn_id": "spark_default",
#     "driver_memory": "1g",
#     "executor_cores": 1,
#     "num_executors": 1,
#     "executor_memory": "1g",
# }

# task that marks the start of this dag
start_task = DummyOperator(task_id="START")

# check configuration task
conf_task = BashOperator(
    task_id="ConfigChecker",
    dag=reporter,
    bash_command="python ${AIRFLOW_HOME}/lib/src/check_conf.py "
    + f"{google_drive_confs}",
    do_xcom_push=True,
)

# load and analyze log task
log_task = BashOperator(
    task_id="LogProcessor",
    dag=reporter,
    bash_command="python ${AIRFLOW_HOME}/lib/src/load_log.py" + f" {google_drive_logs}",
    do_xcom_push=True,
)
# log_task = SparkSubmitOperator(
#     task_id="LogProcessor",
#     dag=reporter,
#     application="src/load_log.py",
#     application_args=google_drive_logs,
#     **spark_conf,
# )


# task to decide what to execute next
def branch(ti):
    if ti.xcom_pull(task_ids="ConfigChecker"):
        return ["push_sns"]
    else:
        return "END"


send_sns_or_not_task = BranchPythonOperator(
    task_id="ConfSnsBranch", python_callable=branch
)

# send notification regarding configuration sanity check result
sns_task = SnsPublishOperator(
    task_id="push_sns",
    target_arn="arn:aws:sns:us-east-2:014912904416:ConfSanityCheck",
    # subject=f"Report on {google_drive_confs}",
    message="{{ task_instance.xcom_pull(task_ids='ConfigChecker') }}",
    dag=reporter,
    aws_conn_id="Jon_AWS",
)

# task that marks one completion of this dag
end_task = DummyOperator(task_id="END", trigger_rule="none_failed_or_skipped")
#############################################
# pipeline architecture
start_task >> log_task
start_task >> conf_task >> send_sns_or_not_task >> [sns_task, end_task]
sns_task >> end_task
#############################################


# demo
# def demo1():
#     print("Hello World")
# def demo2():
#     print("Hello World Again")
# demo_task1 = PythonOperator(task_id="demo1", python_callable=demo1, dag=reporter)
# demo_task2 = PythonOperator(task _id="demo2", python_callable=demo2, dag=reporter)
# demo_task1 >> demo_task2


# uncomment for testing
# if __name__ == "__main__":
#     reporter.cli()
