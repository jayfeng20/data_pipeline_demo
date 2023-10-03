import pyspark as spark
from pyspark.sql import SparkSession
from airflow.operators.python import PythonOperator

# from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime
import library as lib
import sys


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Incorrect number of arguments.")
        print("Usage: file_name.py <log_file_path>")
        sys.exit(1)

    print("Checking logs..")

    try:
        spark = SparkSession.builder.appName("Log Loader").getOrCreate()
        path = sys.argv[1]
        log = spark.read.option("header", "true").csv(path)
        log = lib.fix_header(log)
        spark.stop()
        print("Task completed.")

        # push to xcom by being the last line printed
        print("Log Loaded")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
