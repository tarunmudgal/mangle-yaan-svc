#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest fixtures library """

__author__ = "tarun mudgal"

import json
import os
import time

import boto3
import pytest

from lib import params
from lib.mangle import resources

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


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # pick pytest-html filepath dynamically
    if not config.option.htmlpath:
        config.option.htmlpath = (
            myconfig.get("mangleYaan")
            .get("testReportPath")
            .format(timeStamp=mycache.get("test_start_timestamp"))
        )
        config.option.self_contained_html = True

        # updating final htmlpath to my.json
        myconfig["mangleYaan"]["testReportPath"] = config.option.htmlpath


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
        nonlocal taskid_to_remediate  # specifes var to be picked up from nearest outer scope

        request_body = {
            "endpointName": endpoint_name,
            "resourceName": resource_name,
            "randomInjection": random_injection,
        }

        task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
            "POST", resources.INFRA_FAULTS.get("K8S_SERVICE_UNAVAILABLE"), json=request_body
        )
        mylog.debug(
            "task for K8S_SERVICE_UNAVAILABLE fault triggered with task_id={}, task_status={}".format(
                task_id, task_status
            )
        )
        assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]
        taskid_to_remediate = task_id

        return

    # returns this func when fixture is called. Post test case execution, performs post yield section as teardown
    yield _inject_k8s_infra_fault_service_unavailable

    mylog.debug(
        "let's give some time to mangle before triggering remediation task. waiting for 120 secs"
    )
    time.sleep(120)

    api_resource = resources.OTHER_FAULTS.get("REMEDIATION") + "/" + taskid_to_remediate
    task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
        "DELETE", api_resource
    )
    mylog.debug(
        "task for K8S_SERVICE_UNAVAILABLE fault remediation triggered with task_id={}, task_status={}".format(
            task_id, task_status
        )
    )
    assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]


@pytest.fixture(scope="class")
def inject_k8s_infra_fault_service_unavailable_for_am():
    request_body = {
        "endpointName": myconfig.get("k8sCluster").get("endpointName"),
        "resourceName": "csp-account-management-mvc",
        "randomInjection": False,
    }

    task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
        "POST", resources.INFRA_FAULTS.get("K8S_SERVICE_UNAVAILABLE"), json=request_body
    )
    mylog.debug(
        "task for K8S_SERVICE_UNAVAILABLE fault triggered with task_id={}, task_status={}".format(
            task_id, task_status
        )
    )
    assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]

    yield  # post yield runs as the part of teardown

    mylog.debug(
        "let's give some time to mangle before triggering remediation task. waiting for 60 secs"
    )
    time.sleep(60)

    api_resource = resources.OTHER_FAULTS.get("REMEDIATION") + "/" + task_id
    task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
        "DELETE", api_resource
    )
    mylog.debug(
        "task for K8S_SERVICE_UNAVAILABLE fault remediation triggered with task_id={}, task_status={}".format(
            task_id, task_status
        )
    )
    assert task_status == params.MANGLE_TASK_STATUS["COMPLETED"]
