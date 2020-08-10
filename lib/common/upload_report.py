import os
import sys

import boto3

project_name = os.getenv("project_name", "csp_resiliency")
workload_name = os.getenv("workload_name", "cpu_spike")
run_id = os.getenv("run_id", "abcd")
input_dir = "maxim-gun/" + project_name + "/" + workload_name + "/" + run_id + "/inputs"
bucket_name = "csp-e2e-qe"
print("uploading result file to S3")
s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIAUE4JITGQ3LKSAK5E",
    aws_secret_access_key="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",
)
s3_result_file = (
    "maxim-gun/" + project_name + "/" + workload_name + "/" + run_id + "/results/report.html"
)
s3.upload_file("report.html", bucket_name, s3_result_file)
print("uploaded successfully")
