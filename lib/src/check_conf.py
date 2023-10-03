import pyspark as ps
from pyspark.sql import SparkSession
from airflow.operators.python import PythonOperator
import sys

# from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import library as lib

"""
"usepool": false, indicates that Connection Pooling is turned off. A sub-optimal deployment.
"cacheEnabled": false, = caching has been disabled. another sub-optimal configuration.
and finally the rules section must have a rule to enable r/w split;
all three of these being present confirms the proxy is configured 
to support each of those features: connection pooling, caching, and r/w split.
Then the performance of each of those features can be examined.

"authMode": "passthrough" - use passthrough auth to let the DB do the authenticationp

"""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Incorrect number of arguments.")
        print("Usage: file_name.py <log_file_path>")
        sys.exit(1)

    print("Checking configurations..")
    spark = SparkSession.builder.appName("Config Checker").getOrCreate()
    path = sys.argv[1]
    config = spark.read.option("multiLine", "true").json(path)
    config_handler = lib.sanity_check(config)
    msg_to_send = config_handler.get_msg()
    spark.stop()
    print("Task completed.")

    # push msg_to_send onto Xcom
    # msg_to_send = (
    #     "Configuration sanity check passed!" if not msg_to_send else msg_to_send
    # )
    print(msg_to_send)
    spark.stop()
