# helper function to retrieve Xcom data


def get_xcom(write_to, key, **kwargs):
    ti = kwargs["ti"]
    content = ti.xcom_pull(task_ids=f"{key}")
    write_to = content
