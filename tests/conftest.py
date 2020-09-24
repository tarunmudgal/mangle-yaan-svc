#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest fixtures library """

__author__ = "tarun mudgal"

import json
import os
import time

import boto3
import pytest
from py.xml import html

from lib import params
from lib.mangle import resources


def pytest_html_report_title(report):
    report.title = myconfig.get("projectDescription") + " " + "Report"


def pytest_html_results_summary(prefix, summary, postfix):
    class myhtml(html):
        class p(html.p):
            style = html.Style(font_weight="bold")
    prefix.extend([myhtml.p("{:<30}{}".format("PROJECT NAME:", mycache["project_name"]))])
    prefix.extend([myhtml.p("{:<30}{}".format("WORKLOAD NAME:", mycache["workload_name"]))])
    prefix.extend([myhtml.p("{:<30}{}".format("Test Start Timestamp:", mycache["test_start_timestamp"]))])


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


@pytest.fixture(scope="function")
def inject_k8s_infra_fault_service_unavailable_for_func():
    taskid_to_remediate = None

    def _inject_k8s_infra_fault_service_unavailable_for_func(
        resource_name, random_injection
    ):
        nonlocal taskid_to_remediate  # specifes var to be picked up from nearest outer scope

        request_body = {
            "endpointName": myconfig.get("k8sCluster").get("endpointName"),
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
    yield _inject_k8s_infra_fault_service_unavailable_for_func

    mylog.debug(
        "let's give some time to mangle before triggering remediation task. waiting for 60 secs"
    )
    time.sleep(60)

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
def inject_k8s_infra_fault_service_unavailable_for_class(request):

    faulty_svc_name = request.param

    request_body = {
        "endpointName": myconfig.get("k8sCluster").get("endpointName"),
        "resourceName": faulty_svc_name,
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

    yield faulty_svc_name # post yield runs as the part of teardown

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
