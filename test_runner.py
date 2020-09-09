#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" resiliency test runner """

__author__ = "tarun mudgal"

import argparse
import builtins
import datetime
import inspect
import logging
import os
import pprint
import sys
import typing

import boto3
import pytest
import requests

from lib.common import config_reader, logger
from lib.common import resources as common_resources
from lib.common import rest_client
from lib.csp import csp_client
from lib.csp import resources as csp_resources
from lib.mangle import endpoint, mangle_client

requests.packages.urllib3.disable_warnings()
# logging.getLogger("urllib3").setLevel(logging.WARNING)

# constants initialization
ROOT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
builtins.ROOT_DIR = ROOT_DIR

LOG_DIR = ROOT_DIR + os.path.sep + "logs"
CONF_DIR = ROOT_DIR + os.path.sep + "config"
TESTSUITES_DIR = ROOT_DIR + os.path.sep + "tests"
SRC_DIR = ROOT_DIR + os.path.sep + "src"
TESTLIB_DIR = ROOT_DIR + os.path.sep + "src" + os.path.sep + "testlib"

# create logs dir if not exist
if not os.path.exists(LOG_DIR):
    print("creating log directory: %s" % LOG_DIR, flush=True)
    os.makedirs(LOG_DIR)

# mylog = logger.Log(logger.get_logger())
mylog = logger.get_logger()
builtins.mylog = mylog
mylog.info("logger initialized")


def check_network_availability() -> None:
    """Performs network availability check by making a call to google.com

    Returns:
      None
    """
    request_url = "https://www.google.com"
    resp_code_exp = requests.codes.ok

    try:
        resp = requests.get(request_url, verify=False)
        assert resp.status_code == resp_code_exp
        mylog.info("Network Availability Check: OK")
    except Exception as fault:
        mylog.error("Network Availability Check: Failed")
        mylog.error("Error: %s. Exiting %s" % (fault, sys.argv[0]))
        sys.exit(1)


def prepare_setup(
    myconf_file: str = None, project_name: str = None, workload_name: str = None
) -> None:
    """Performs setup preparation tasks i.e. ensuring network connectivity, reading mangle-yaan
    config file, initializing Mangle and CSP REST clients, creating Mangle endpoint credential
    and endpoint for CSP K8S cluster etc.

    Args:
      myconf_file: mangle-yaan configuration (json) file. If provided, It overrides default config file config/my.json
      project_name: project name created on maxim-gun UI
      workload_name: workload name created on maxim-gun UI

    Returns:
      None
    """
    check_network_availability()

    # read mangle-yaan config (my.json). Looks up in environment vars if set else pick-up the default value
    # conf_file = os.getenv("MYCONFIG", CONF_DIR + os.path.sep + "my.json")

    # read static config
    my_json = CONF_DIR + os.path.sep + "my.json"
    my_json = config_reader.parse_json(my_json)

    myconfig = None
    # read mangle-yaan config from command line
    if myconf_file is not None:
        conf_file = myconf_file
        mylog.debug("reading config locally from path={}".format(conf_file))
        myconfig = config_reader.parse_json(conf_file)

    # read mangle-yaan config from maxim-gun api (from maxim_gun.workload table)
    else:
        mg_base_url = (
            "http://" + my_json.get("maximGun").get("host") + common_resources.MAXIMGUN_RES_API_PREFIX
        )
        api_resource = common_resources.MAXIMGUN.get("MANGLEYAAN_CONFIG")
        myconfig_url = mg_base_url + api_resource
        params = {"workload_name": workload_name}

        mylog.debug("reading config from maxim-gun app. url={}".format(myconfig_url))

        response = rest_client.request(
            "GET", myconfig_url, retry_count=1, retry_sleep=5, params=params
        )
        if response.status_code == requests.codes.ok:
            res_json = response.json()
            myconfig = res_json.get("mangle_yaan_conf")
            # mylog.debug("maxim-gun api json response={}".format(res_json))
        else:
            mylog.error(
                "failed to read config from maxim-gun app. Request(url={}, params={}). Response(status={}, text={})".format(
                    myconfig_url, params, response.status_code, response.text
                )
            )
            sys.exit(2)

    builtins.myconfig = myconfig
    mangle_conf = myconfig.get("mangle")
    mclient = mangle_client.MangleClient(
        mangle_conf.get("host"),
        mangle_conf.get("username"),
        mangle_conf.get("password"),
        timeout=120,
    )
    builtins.mclient = mclient

    csp_conf = myconfig.get("csp")
    cclient = csp_client.CSPClient(
        csp_conf.get("host"),
        csp_conf.get("defaultUser").get("refreshToken"),
        timeout=120,
    )
    builtins.cclient = cclient

    ep_cred = endpoint.EndpointCredential(mclient)
    does_cred_exist = False
    status, response = ep_cred.list_credentials()
    if not status:
        mylog.error("Failed to fetch credentials from mangle")
        sys.exit(2)
    else:
        for cred in response.json:
            if cred.get("name") == myconfig.get("k8sCluster").get("credentialName"):
                does_cred_exist = True
    if not does_cred_exist:
        status, response = ep_cred.create_credential_k8s_cluster(
            myconfig.get("k8sCluster").get("credentialName"),
            myconfig.get("k8sCluster").get("kubeConfigFileName"),
        )
        if not status:
            mylog.error(
                "Failed to create k8s cluster credential for credentialName={}, kubeConfigFileName={}".format(
                    myconfig.get("k8sCluster").get("credentialName"),
                    myconfig.get("k8sCluster").get("kubeConfigFileName"),
                )
            )
            sys.exit(2)
        mylog.info(
            "credential '{}' for k8s cluster created successfully".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )
    else:
        mylog.info(
            "credential '{}' for k8s cluster already exist".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )

    epoint = endpoint.Endpoint(mclient)
    does_endpoint_exist = False
    status, response = epoint.list_endpoints_k8s_cluster()
    if not status:
        mylog.error("Failed to fetch endpoints from mangle")
        sys.exit(2)
    else:
        for ep in response.json:
            if ep.get("name") == myconfig.get("k8sCluster").get("endpointName"):
                does_endpoint_exist = True
    if not does_endpoint_exist:
        status, response = epoint.create_endpoint_k8s_cluster(
            myconfig.get("k8sCluster").get("endpointName"),
            myconfig.get("k8sCluster").get("credentialName"),
            myconfig.get("k8sCluster").get("namespace"),
        )
        if not status:
            mylog.error(
                "Failed to create k8s cluster endpoint for endpointName={}, credentialName={}, namespace={}".format(
                    myconfig.get("k8sCluster").get("endpointName"),
                    myconfig.get("k8sCluster").get("credentialName"),
                    myconfig.get("k8sCluster").get("namespace"),
                )
            )
            sys.exit(2)
        mylog.info(
            "endpoint '{}' for k8s cluster created successfully".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )
    else:
        mylog.info(
            "Endpoint '{}' for k8s cluster already exist".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )

    tc = endpoint.TestConnection(mclient)
    status, response = tc.test_endpoint(myconfig.get("k8sCluster").get("endpointName"))
    if not status:
        mylog.error(
            "Test connection for endpoint {} failed".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )
        sys.exit(2)
    else:
        mylog.info(
            "Test connection for endpoint {} passed".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )

    # test_runner cache to maintain states
    mycache = {}
    builtins.mycache = mycache

    # adding project_name and workload_name into mycache to use them in pytest-html greport generation
    mycache["project_name"] = project_name
    mycache["workload_name"] = workload_name

    mylog.info("setup is ready to run resiliency tests now")


def run_pytest(*args, **kwargs):
    # start_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    start_ts = datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S.%f")
    mycache.update({"test_start_timestamp": start_ts})
    mylog.info("starting pytest test cases execution at: %s" % start_ts)

    status = pytest.main(*args, **kwargs)

    # end_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    end_ts = datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S.%f")
    mycache.update({"test_end_timestamp": end_ts})
    mylog.info("pytest test cases execution finished at: %s" % end_ts)

    return status


def post_run_activities(copy_results: bool = True) -> None:
    """Tasks to be performed after pytest test-suites execution

    Args:
      copy_results: flag for enabling/disabling pytest test results copy on S3 bucket

    Returns:
      None
    """
    if copy_results:
        copied_successfully, failed_to_copy = copy_files_on_s3(
            bucket_name=myconfig.get("aws").get("s3").get("bucketName"),
            file_paths=[myconfig.get("mangleYaan").get("testReportPath")],
        )
        if failed_to_copy:
            mylog.error("test reports = {} could not be copied over S3".format(failed_to_copy))
        else:
            mylog.info("test reports = {} copied successfully over S3".format(copied_successfully))


def copy_files_on_s3(bucket_name: str, file_paths: typing.List[str] = None) -> typing.List[str]:
    """copies files on S3 bucket

    Args:
      bucket_name: S3 bucket name
      file_paths: list of file-paths that need to be copied to S3 bucket

    Returns:
      copied_successfully: list of file-paths that copied successfully
      failed_to_copy: list of file-paths that failed to copy
    """
    copied_successfully = []
    failed_to_copy = []

    if file_paths:
        s3_conf = myconfig.get("aws").get("s3")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=s3_conf.get("awsAccessKeyID"),
            aws_secret_access_key=s3_conf.get("awsSecretAccessKey"),
        )
        for fpath in file_paths:
            fname = os.path.basename(fpath)
            try:
                s3_client.upload_file(
                    Filename=fpath,
                    Bucket=bucket_name,
                    Key="{}{}".format(s3_conf.get("testReportPath"), fname),
                )
                copied_successfully.append(fpath)
            except Exception as fault:
                failed_to_copy.append(fpath)
                mylog.debug("file {} could not be copied on S3. Error={}".format(fpath, fault))

    else:
        mylog.debug("nothing to copy on S3")

    return copied_successfully, failed_to_copy


def get_test_modules_from_testsuite_names(testsuite_names: str) -> typing.List[str]:
    """verifies test-suites exist in testsuites_info.json and returns corresponding test-module file-paths.
    test-suites are a bit user-friendly names. They are mapped with test-modules in testsuites_info.json file.

    Note: All test-modules should have an mapping (test-suite->test-module) in testsuites_info.json file.

    Args:
      testsuite_names: comma separated list of test_suite names

    Returns:
      testmodule_paths: list of test-module paths
    """
    testsuites_info_file = TESTLIB_DIR + os.path.sep + "testsuites_info.json"
    testsuites_info = config_reader.parse_json(testsuites_info_file)

    # removes empty-string/white-spaces-only test-suite names if any
    testsuite_names = testsuite_names.split(",")
    testsuite_names = [ts for ts in testsuite_names if ts.strip() != ""]

    testmodule_paths = []
    for ts_name in testsuite_names:
        if ts_name in testsuites_info:
            testmodule_paths.append(testsuites_info.get(ts_name).get("path"))
        else:
            mylog.error(
                "testsuite name {} does not exist. Available testsuite names are {}".format(
                    ts_name, testsuites_info.keys()
                )
            )
            sys.exit(1)

    return testmodule_paths


def print_testsuite_info() -> None:
    """prints available testsuites names

    Returns:
        None
    """
    testsuites_info_file = TESTLIB_DIR + os.path.sep + "testsuites_info.json"
    testsuites_info = config_reader.parse_json(testsuites_info_file)

    testsuite_names = pprint.pformat(list(testsuites_info.keys()))
    print("Available testsuites are:\n{}\n".format(testsuite_names))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""resiliency test suite execution driver""")
    parser.add_argument(
        "--project_name", action="store", type=str, help="project name created on maxim-gun UI",
    )
    parser.add_argument(
        "--workload_name", action="store", type=str, help="workload name created on maxim-gun UI",
    )
    parser.add_argument(
        "--testsuite_names",
        # nargs="+",
        action="store",
        type=str,
        help="Specify list of space separated testsuite names",
    )
    parser.add_argument(
        "--myconfig",
        action="store",
        type=str,
        help="mangle-yaan config file path. If this option is used, "
        "it will ovverride default config file config/my.json",
    )
    parser.add_argument(
        "--pytest_args",
        action="store",
        type=str,
        default="",
        help="pytest args that will be passed to pytest as it is. All pytest args should be passed in one string",
    )
    parser.add_argument(
        "--list_testsuite_names", action="store_true", help="list of available testsuites",
    )

    args = parser.parse_args()
    mylog.debug("test_runner args={}".format(args))

    if args.list_testsuite_names:
        print_testsuite_info()
        sys.exit(0)

    if args.project_name is None or args.project_name == "":
        print(
            "--project_name is required to trigger test execution. It will be used to fetch mangle-yaan configuration"
        )
        sys.exit(1)

    if args.workload_name is None or args.workload_name == "":
        print(
            "--workload_name is required to trigger test execution. It will be used to fetch mangle-yaan configuration"
        )
        sys.exit(1)

    if args.testsuite_names is None or args.testsuite_names == "":
        print(
            "--testsuite_names is required to trigger test execution. If you are not sure about testsuite name, "
            "please use --list_testsuite_names to get the list of available testsuites"
        )
        sys.exit(1)

    pytest_cmdline = []
    if args.pytest_args is not None:
        # removes leading and trailing single/double quotes, white-spaces from args.pytest_args
        args.pytest_args = args.pytest_args.strip()
        args.pytest_args = args.pytest_args.strip("'")
        args.pytest_args = args.pytest_args.strip('"')

        pytest_cmdline += args.pytest_args.split()

    testsuite_paths = get_test_modules_from_testsuite_names(args.testsuite_names)
    pytest_cmdline += testsuite_paths

    prepare_setup(
        myconf_file=args.myconfig, project_name=args.project_name, workload_name=args.workload_name
    )
    pytest_status = run_pytest(pytest_cmdline)

    # don't copy logs to S3 for pytest usage error. seems incorrect --pytest_args are passed
    copy_results = True
    if pytest_status == 4:
        copy_results = False
    post_run_activities(copy_results=copy_results)
