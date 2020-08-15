#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest fixtures library """

__author__ = "tarun mudgal"

import json
import os
import time

import boto3
import pytest
from lib.mangle import resources
from lib.csp import resources as csp_resources
from lib import params

from py.xml import html

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


def pytest_html_report_title(report):
    report.title = myconfig.get("projectDescription") + " " + "Report"


def download_s3_file():
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    print("downloading file from S3")
    s3.download_file(bucket_name, input_dir + "/fault.csv", input_dir + "/fault.csv")


# @pytest.fixture(scope="session")
def get_fault_end_ts():
    download_s3_file()
    with open(input_dir + "/fault.csv") as f:
        fault_vals = json.loads(f.read())
        yield fault_vals["fault_end_timestamp"]



@pytest.fixture(scope="function")
def inject_k8s_infra_fault_service_unavailable():
    taskid_to_remediate = None

    def _inject_k8s_infra_fault_service_unavailable(
            endpoint_name, resource_name, random_injection
    ):
        nonlocal taskid_to_remediate

        request_body = {
            "endpointName": endpoint_name,
            "resourceName": resource_name,
            "randomInjection": random_injection,
        }

        task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
            "POST", resources.INFRA_FAULTS.get("K8S_SERVICE_UNAVAILABLE"), json=request_body
        )
        mylog.debug(
            "task for K8S_SERVICE_UNAVAILABLE fault triggered with task_id={}, task_status={}".format(task_id, task_status))
        assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]
        taskid_to_remediate = task_id

        return

    yield _inject_k8s_infra_fault_service_unavailable

    time.sleep(120) # let's give some time before triggering remediation task

    api_resource = resources.OTHER_FAULTS.get("REMEDIATION") + "/" + taskid_to_remediate
    task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
        "DELETE", api_resource
    )
    mylog.debug(
        "task for K8S_SERVICE_UNAVAILABLE fault remediation triggered with task_id={}, task_status={}".format(task_id, task_status))
    assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]
