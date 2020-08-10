import json
import os

import boto3
import pytest

# log = logger.setup_logging(__name__)

ROOT_USER = "root"
SCHEDULE_CRON_EXP = None
SCHEDULE_EPOCH_TIME = None
TAGS = {}


project_name = os.getenv("project_name", "csp_resiliency")
workload_name = os.getenv("workload_name", "cpu_spike")
run_id = os.getenv("run_id", "abcd")
input_dir = "maxim-gun/" + project_name + "/" + workload_name + "/" + run_id + "/inputs"
s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIAUE4JITGQ3LKSAK5E",
    aws_secret_access_key="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",
)
bucket_name = "csp-e2e-qe"


def download_s3_file():
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    print("downloading file from S3")
    s3.download_file(bucket_name, input_dir + "/fault.csv", input_dir + "/fault.csv")


@pytest.fixture(scope="session")
def get_fault_end_ts():
    download_s3_file()
    with open(input_dir + "/fault.csv") as f:
        fault_vals = json.loads(f.read())
        yield fault_vals["fault_end_timestamp"]
