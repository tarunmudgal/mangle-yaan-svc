#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest fixtures library """

__author__ = "tarun mudgal"

import io
import os
import time
from collections import OrderedDict

import pytest
import requests
from py.xml import html
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from lib import params as lib_params
from lib.common import utils
from lib.mangle import resources
from lib.csp import resources as csp_resources
from lib.maximgun import resources as maxim_gun_resources
from src.testlib import params as testlib_params


def pytest_html_report_title(report):
    """
    hook to modify pytest-html report title
    """
    report.title = myconfig.get("projectDescription") + " " + "Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """
    hook to modify pytest-html results summary
    """

    class myhtml(html):
        class p(html.p):
            style = html.Style(font_weight="bold")

    prefix.extend(
        [myhtml.p("{:<30}{}".format("PROJECT NAME:", mycache["run_info"]["project_name"]))]
    )
    prefix.extend(
        [myhtml.p("{:<30}{}".format("WORKLOAD NAME:", mycache["run_info"]["workload_name"]))]
    )
    prefix.extend(
        [
            myhtml.p(
                "{:<30}{}".format(
                    "Test Start Timestamp:", mycache["run_info"]["test_start_timestamp"]
                )
            )
        ]
    )


@pytest.mark.optionalhook
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th("Description"))


@pytest.mark.optionalhook
def pytest_html_results_table_row(report, cells):
    cells.insert(1, html.td(report.description))


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    """
    Extends the PyTest Plugin to take and embed screenshot in html report, whenever test fails.
    :param item:
    """
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)
    extra = getattr(report, "extra", [])

    if report.when == "call" and "init_chrome_driver" in item.funcargs:
        # extra.append(pytest_html.extras.url('http://www.example.com/'))
        xfail = hasattr(report, "wasxfail")
        if (report.skipped and xfail) or (report.failed and not xfail):
            request_ctx = item.funcargs["request"]
            # driver = request_ctx.getfixturevalue('init_chrome_driver')
            driver = getattr(request_ctx.cls, "driver", None)
            if driver is not None:
                screenshot = driver.get_screenshot_as_base64()
                extra.append(pytest_html.extras.image(screenshot, ""))
                # extra.append(pytest_html.extras.html('<div>Additional HTML</div>'))
        report.extra = extra


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    From Pytest doc:
    Allow plugins and conftest files to perform initial configuration. This hook is called for every
    plugin and initial conftest file after command line options have been parsed.
    Here, we are using it to pick pytest-html filepath dynamically
    """
    if not config.option.htmlpath:
        config.option.htmlpath = (
            myconfig.get("mangleYaan")
                .get("testReportPath")
                .format(timeStamp=mycache["run_info"].get("test_start_timestamp"))
        )
        config.option.self_contained_html = True

        # updating final htmlpath to my.json
        myconfig["mangleYaan"]["testReportPath"] = config.option.htmlpath

    if not config.option.allure_report_dir:
        config.option.allure_report_dir = lib_params.ALLURE_LOG_DIR + os.path.sep + "raw"


@pytest.fixture(scope="function", autouse=True)
def check_if_user_cancelled_execution():
    """
    this fixture is called for each function. It captures if user has cancelled workload execution from maxim-gun UI
    """
    if mycache["run_info"]["run_id"]:
        params = {"run_id": mycache["run_info"]["run_id"]}
        resp = mgclient.make_call(
            "GET", maxim_gun_resources.MAXIMGUN.get("GET_TASK_STATUS"), params=params
        )
        if resp.status_code == requests.codes.ok:
            if resp.json["status"] == lib_params.MG_TASK_STATUS["CANCELLED"]:
                pytest.exit(msg="Pytest Cancelled by User", returncode=2)
        else:
            mylog.error(
                "maxim-gun GET_TASK_STATUS API failed with status_code={}".format(resp.status_code)
            )


def pytest_sessionfinish(session, exitstatus):
    """
    hook to perform some task during pytest session finish. we are using it to calculate aggregate result and
    accordingly colour coding (GREEN/YELLOW/RED) would be added for workload run on maxim-gun UI
    """
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    flaky_plugin = session.config.pluginmanager.get_plugin("flaky")
    result_summary = OrderedDict()
    result_summary["passed"] = len(reporter.stats.get("passed", []))
    result_summary["failed"] = len(reporter.stats.get("failed", []))
    result_summary["skipped"] = len(reporter.stats.get("skipped", []))

    passing_percent = utils.get_mangleyaan_passing_test_percent(result_summary)
    aggregatd_result = utils.get_mangleyaan_result_status(passing_percent)

    result_summary["passing_percent"] = passing_percent
    result_summary["aggregatd_result"] = aggregatd_result

    mylog.info("current test execution result_summary={}".format(result_summary))

    mycache["run_info"]["result_summary"] = result_summary

    flaky_output = io.StringIO()
    flaky_plugin.pytest_terminal_summary(flaky_output)
    mylog.info("flaky plugin execution report=\n{}".format(flaky_output.getvalue()))

    allure_report_dir = session.config.option.allure_report_dir
    env_details = """my.properties.browser=Firefox
my.properties.url=http://yandex.ru"""  # .format(mycache["run_info"]["workload_name"])

    if allure_report_dir:
        with open('{}/{}'.format(allure_report_dir, 'environment.properties'), 'w') as allure_env:
            allure_env.write("{}".format(env_details))


@pytest.fixture(scope="function")
def inject_k8s_infra_fault_service_unavailable_for_func():
    taskid_to_remediate = None
    service_name = None

    def _inject_k8s_infra_fault_service_unavailable_for_func(resource_name, random_injection):
        nonlocal taskid_to_remediate, service_name  # specifes var to be picked up from nearest outer scope

        service_name = resource_name

        # mangle fault injection
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

    try:
        # mangle fault remediation
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
    except Exception as fault:
        mylog.info(
            "Exception occurred while remediating mangle infra fault for service={}. Exception={}".format(
                service_name, fault
            )
        )

        # fallback mechanism to remediate fault if mangle fails to do so
        service_info = ckclient.get_service(service_name)
        if service_info.spec.selector["environment"] == "mangle":
            mylog.info(
                "Let's try to remediate mangle infra fault using K8S API for service={}".format(
                    service_name
                )
            )
            service_info.spec.selector["environment"] = (
                myconfig.get("k8sCluster").get("namespace").split("-")[2]
            )
            ckclient.patch_service(service_name, service_info)
            mylog.info(
                "mangle infra fault remediated successfully for service={} using K8S API".format(
                    service_name
                )
            )
        else:
            mylog.info(
                "mangle infra fault seems to be remediated already for service={}".format(
                    service_name
                )
            )


@pytest.fixture(scope="function")
def inject_k8s_infra_fault_abrupt_pod_shutdown_for_func(request):
    resource_labels = request.cls.resource_labels
    random_injection = request.cls.random_injection
    sleep_interval = request.cls.sleep_interval

    pod_shutdown_event_handler = mclient.trigger_abrupt_pod_shutdown_fault_repetatively(
        resource_labels, random_injection, sleep_interval
    )

    yield

    pod_shutdown_event_handler.set()


@pytest.fixture(scope="class")
def inject_k8s_app_fault_spring_service_latency_for_class(request, scale_deployments_for_class):
    service_latency = request.cls.SERVICE_LATENCY
    service_method_verb = request.cls.SERVICE_METHOD_VERB
    service_uri = request.cls.SERVICE_URI
    container_name = request.cls.CONTAINER_NAME
    pod_labels = request.cls.POD_LABELS
    random_injection = request.cls.RANDOM_INJECTION
    java_home_path = request.cls.JAVA_HOME_PATH
    port = request.cls.PORT

    deployment_names = request.module.DEPLOYMENT_NAMES_TO_BE_SCALED
    new_replica_count = request.module.NEW_REPLICA_COUNT

    status, pod_names = ckclient.wait_for_pods_to_update_state(new_replica_count, label_selector=pod_labels,
                                            field_selector="status.phase=Running")

    pod_info = {}
    if status:
        for pod_name in pod_names:
            jvm_process_id = ckclient.execute_cmd_inside_pod(pod_name, 'pgrep java')
            pod_info[pod_name] = {'process_id': jvm_process_id}

            # mangle fault injection
            request_body = {
                "endpointName": myconfig.get("k8sCluster").get("endpointName"),
                "injectionHomeDir": "/tmp/",
                "latency": service_latency,
                "servicesString": service_uri,
                "httpMethodsString": service_method_verb,
                "k8sArguments": {
                    "containerName": container_name,
                    "podLabels": pod_labels,
                    "enableRandomInjection": random_injection
                },
                "jvmProperties": {
                    "javaHomePath": java_home_path,
                    "jvmprocess": jvm_process_id,
                    "port": port
                }
            }

            task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
                "POST", resources.APP_FAULTS.get("SPRING_SERVICE_LATENCY"), json=request_body
            )

            pod_info[pod_name]['fault_task_id'] = task_id
            pod_info[pod_name]['fault_task_status'] = task_status

            mylog.debug(
                "task for SPRING_SERVICE_LATENCY fault triggered with task_id={}, task_status={}".format(
                    task_id, task_status
                )
            )
            assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]

            status = mclient.wait_for_child_tasks_to_finish(task_id)
            assert status
    else:
        request.module.DEPLOYMENTS_COULD_NOT_BE_SCALED = True

    yield  # post yield runs as the part of teardown

    if status:
        mylog.debug(
            "let's give some time to mangle before triggering remediation task. waiting for 60 secs"
        )
        time.sleep(60)

        for pod_name in pod_info:
            try:
                # mangle fault remediation
                api_resource = resources.OTHER_FAULTS.get("REMEDIATION") + "/" + pod_info[pod_name]['fault_task_id']
                task_id, task_status = mclient.trigger_fault_task_and_wait_for_completion(
                    "DELETE", api_resource
                )
                mylog.debug(
                    "task for SPRING_SERVICE_LATENCY fault remediation triggered with task_id={}, task_status={}".format(
                        task_id, task_status
                    )
                )
                assert task_status == lib_params.MANGLE_TASK_STATUS["COMPLETED"]
            except Exception as fault:
                mylog.info(
                    "Exception occurred while remediating mangle SPRING_SERVICE_LATENCY fault with id={}. Exception={"
                    "}".format(
                        pod_info[pod_name]['fault_task_id'], fault
                    )
                )


@pytest.fixture(scope="class")
def inject_k8s_infra_fault_service_unavailable_for_class(request):
    faulty_svc_name = request.param

    # mangle fault injection
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

    try:
        # mangle fault remediation
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
    except Exception as fault:
        mylog.info(
            "Exception occurred while remediating mangle infra fault for service={}. Exception={}".format(
                faulty_svc_name, fault
            )
        )

        # fallback mechanism to remediate fault if mangle fails to do so
        service_info = ckclient.get_service(faulty_svc_name)
        if service_info.spec.selector["environment"] == "mangle":
            mylog.info(
                "Let's try to remediate mangle infra fault using K8S API for service={}".format(
                    faulty_svc_name
                )
            )
            service_info.spec.selector["environment"] = (
                myconfig.get("k8sCluster").get("namespace").split("-")[2]
            )
            ckclient.patch_service(faulty_svc_name, service_info)
            mylog.info(
                "mangle infra fault remediated successfully for service={} using K8S API".format(
                    faulty_svc_name
                )
            )
        else:
            mylog.info(
                "mangle infra fault seems to be remediated already for service={}".format(
                    faulty_svc_name
                )
            )


@pytest.fixture(scope="class")
def inject_k8s_infra_fault_block_egress_traffic_for_class(request):
    network_policy_filename = request.param

    mylog.debug("creating a network policy using {} file".format(network_policy_filename))
    response_create, error = ckclient.create_network_policy(network_policy_filename)
    assert error is None
    assert response_create.metadata
    mylog.debug(
        "network policy {} created successfully using {} file".format(
            response_create.metadata.name, network_policy_filename
        )
    )

    yield network_policy_filename  # post yield runs as the part of teardown

    mylog.debug("deleting network policy {}".format(response_create.metadata.name))
    response_delete, error = ckclient.delete_network_policy(response_create.metadata.name)
    assert error is None
    assert response_delete.status == "Success"
    mylog.debug("network policy {} deleted successfully".format(response_delete.details.name))


@pytest.fixture(scope="class")
def scale_deployments_for_class(request):
    deployment_names = request.module.DEPLOYMENT_NAMES_TO_BE_SCALED
    new_replica_count = request.module.NEW_REPLICA_COUNT

    deployments_replica_map_prev = {}
    deployments_replica_map_next = {}

    for dep_name in deployment_names:
        deployment_info = ckclient.get_deployment(dep_name)
        deployments_replica_map_prev[dep_name] = deployment_info.spec.replicas
        deployments_replica_map_next[dep_name] = new_replica_count

    status, deployments_not_scaled = ckclient.scale_deployments(
        deployments_replica_map_next, timeout=600
    )
    if deployments_not_scaled:
        request.module.DEPLOYMENTS_COULD_NOT_BE_SCALED = True

    # performs post yield section as teardown
    yield

    ckclient.scale_deployments(deployments_replica_map_prev, timeout=900)


@pytest.fixture(scope="class")
def update_csp_access_token():
    cclient.update_access_token()


@pytest.fixture(scope="class")
def init_chrome_driver(request):
    if myconfig.get("mangleYaan").get("webDriver").get("initLocal"):
        driver = webdriver.Chrome(
            myconfig.get("mangleYaan").get("webDriver").get("chromeDriverPath")
        )
    else:
        # driver = webdriver.Remote(command_executor='http://selenium-mangle-yaan.svc-stage.eng.vmware.com:31001/wd/hub'
        #                                           , desired_capabilities=getattr(DesiredCapabilities, "CHROME"))
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
    driver.implicitly_wait(testlib_params.WEBDRIVER_IMPLICIT_WAIT)
    driver.maximize_window()

    # assign driver as a class variable to the class consuming fixture
    request.cls.driver = driver

    yield driver

    driver.quit()



def get_kong_gateway_api_req_termination_details():
    api_resource = csp_resources.FF.get("GET_CSP_FF_ENVIRONMENTS").format(
        orgId=myconfig.get("csp").get("defaultOrg").get("id")
    )

    com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

    if com_resp.json is not None:
        envIds = [eachEnv["id"] for eachEnv in com_resp.json.get("results")]
    return envIds

@pytest.fixture(scope="class")
def test_csp_ui_when_kong_gateway_commerce_api_is_blocked():
    envIds = get_kong_gateway_api_req_termination_details()

    api_resource = csp_resources.FF.get("PATCH_CSP_API_GATEWAY_REQUEST_TERMINATION_FLAG").format(
        orgId=myconfig.get("csp").get("defaultOrg").get("id"),envId=envIds[0]
    )

    request_body = {            
        "multivariateToggle": {
            "defaultValues": {
                "enabled": "conf",
                "disabled": "conf"
            },
            "toggleOptions": [
                {
                    "value": "conf",
                    "metadata": {
                        "paths": [
                            {
                                "path": "/csp/gateway/commerce/api",
                                "body": "VMware Cloud commerce Services is undergoing scheduled maintenance right now.",
                                "exclude": []
                            }
                        ]
                    }
                },
                {
                    "value": "na"
                }
            ]
        }
    }
    
    resp = cclient.make_call(
      "PATCH", api_resource, json=request_body, retry_count=0, disable_implicit_retry=True
    )


    yield resp

    request_body = {
        "multivariateToggle": {
            "defaultValues": {
                "enabled": "conf",
                "disabled": "conf"
            },
            "toggleOptions": [
                {
                    "value": "conf",
                    "metadata": {
                        "paths": []
                    }
                },
                {
                    "value": "na"
                }
            ]
        }
    }

    resp = cclient.make_call(
        "PATCH", api_resource, json=request_body, retry_count=0, disable_implicit_retry=True
    )    

