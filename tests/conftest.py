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
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from lib import params as lib_params
from lib.mangle import resources
from lib.maximgun import agent as mg_agent
from lib.maximgun import maximgun_client as maxim_client
from lib.maximgun import resources as maxim_gun_resources
from src.testlib import params as testlib_params


def pytest_html_report_title(report):
    report.title = myconfig.get("projectDescription") + " " + "Report"


def pytest_html_results_summary(prefix, summary, postfix):
    class myhtml(html):
        class p(html.p):
            style = html.Style(font_weight="bold")

    prefix.extend([myhtml.p("{:<30}{}".format("PROJECT NAME:", mycache["project_name"]))])
    prefix.extend([myhtml.p("{:<30}{}".format("WORKLOAD NAME:", mycache["workload_name"]))])
    prefix.extend(
        [myhtml.p("{:<30}{}".format("Test Start Timestamp:", mycache["test_start_timestamp"]))]
    )


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


@pytest.fixture(scope="function", autouse=True)
def check_if_user_cancelled_execution():
    if mycache["run_id"]:
        params = {"run_id": mycache["run_id"]}
        am_resp = mgclient.make_call(
            "GET", maxim_gun_resources.MAXIMGUN.get("GET_TASK_STATUS"), params=params
        )
        if am_resp.json["status"] == lib_params.MG_TASK_STATUS["CANCELLED"]:
            pytest.exit(msg="Pytest Cancelled by User", returncode=2)


@pytest.fixture(scope="function")
def inject_k8s_infra_fault_service_unavailable_for_func():
    taskid_to_remediate = None

    def _inject_k8s_infra_fault_service_unavailable_for_func(resource_name, random_injection):
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
        assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]
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
    assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]


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
    assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]

    yield faulty_svc_name  # post yield runs as the part of teardown

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
    assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]


@pytest.fixture(scope="class")
def inject_k8s_infra_fault_block_egress_traffic_for_class(request):
    network_policy_filename = request.param

    mylog.debug("creating a network policy using {} file".format(network_policy_filename))
    response_create = ckclient.create_network_policy(network_policy_filename)
    assert response_create.metadata
    mylog.debug(
        "network policy {} created successfully using {} file".format(
            response_create.metadata.name, network_policy_filename
        )
    )

    yield network_policy_filename  # post yield runs as the part of teardown

    mylog.debug("deleting network policy {}".format(response_create.metadata.name))
    response_delete = ckclient.delete_network_policy(response_create.metadata.name)
    assert response_delete.status == "Success"
    mylog.debug("network policy {} deleted successfully".format(response_delete.details.name))


@pytest.fixture(scope="class")
def init_chrome_driver(request):
    # driver = webdriver.Remote(command_executor='http://selenium-mangle-yaan.svc-stage.eng.vmware.com:31001/wd/hub', desired_capabilities=getattr(DesiredCapabilities, "CHROME"))
    selenium_hub_fqdn = (
        "http://"
        + testlib_params.SELENIUM_GRID_HOST
        + ":"
        + testlib_params.SELENIUM_GRID_PORT
        + testlib_params.SELENIUM_HUB_URI
    )
    driver = webdriver.Remote(
        command_executor=selenium_hub_fqdn,
        desired_capabilities=getattr(DesiredCapabilities, "CHROME"),
    )
    request.cls.driver = driver
    yield
    driver.close()
