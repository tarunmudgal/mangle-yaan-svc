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
import time
import typing

import boto3
import pytest
import requests

from lib import params as lib_params
from lib.aws import s3
from lib.common import config_reader, logger, rest_client, utils
from lib.csp import csp_client
from lib.csp import resources as csp_resources
from lib.k8s import k8s_client
from lib.mangle import endpoint, mangle_client
from lib.maximgun import agent as mg_agent
from lib.maximgun import maximgun_client
from lib.maximgun import resources as mg_resources

requests.packages.urllib3.disable_warnings()
# logging.getLogger("urllib3").setLevel(logging.WARNING)

# constants initialization
ROOT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
builtins.ROOT_DIR = ROOT_DIR

lib_params.LOG_DIR = ROOT_DIR + os.path.sep + "logs"
lib_params.CONF_DIR = ROOT_DIR + os.path.sep + "config"
lib_params.TESTSUITES_DIR = ROOT_DIR + os.path.sep + "tests"
lib_params.SRC_DIR = ROOT_DIR + os.path.sep + "src"
lib_params.TESTLIB_DIR = ROOT_DIR + os.path.sep + "src" + os.path.sep + "testlib"
lib_params.ALLURE_LOG_DIR = ROOT_DIR + os.path.sep + "logs" + os.path.sep + "allure"

# create logs dir if not exist
if not os.path.exists(lib_params.LOG_DIR):
    print("creating log directory: %s" % lib_params.LOG_DIR, flush=True)
    os.makedirs(lib_params.LOG_DIR)

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


def create_maxim_gun_client(timeout: int = 120) -> maximgun_client.MGClient:
    """
    creates maxim-gun REST client
    Args:
        timeout: timeout used for REST requests

    Returns:
        MGClient instance
    """
    # read static config
    my_json = lib_params.CONF_DIR + os.path.sep + "my.json"
    my_json = config_reader.parse_json(my_json)

    # maxim-gun client
    mg_conf = my_json.get("maximGun")
    mgclient = maximgun_client.MGClient(mg_conf.get("host"), timeout=timeout,)

    return mgclient


def create_mangle_client(timeout: int = 120) -> mangle_client.MangleClient:
    """
    creates mangle REST client
    Args:
        timeout: timeout used for REST requests

    Returns:
        MangleClient instance
    """
    mangle_conf = myconfig.get("mangle")
    mclient = mangle_client.MangleClient(
        mangle_conf.get("host"),
        mangle_conf.get("username"),
        mangle_conf.get("password"),
        timeout=timeout,
    )

    return mclient


def create_csp_client(timeout: int = 120) -> csp_client.CSPClient:
    """
    creates CSP REST client
    Args:
        timeout: timeout used for REST requests

    Returns:
       CSPClient instance
    """
    csp_conf = myconfig.get("csp")
    cclient = csp_client.CSPClient(
        csp_conf.get("host"), csp_conf.get("defaultUser").get("refreshToken"), timeout=timeout,
    )

    return cclient


def create_csp_k8s_client(kubeconfig_filename: str, namespace: str) -> k8s_client.K8SClient:
    """
    creates CSP Kubernetes client
    Args:
        kubeconfig_filename: kubeconfig file-name for CSP kubernetes cluster
        namespace: namespace for CSP kubernetes cluster

    Returns:
       K8SClient instance
    """
    csp_k8s_client = k8s_client.K8SClient(kubeconfig_filename, namespace)

    return csp_k8s_client


def create_s3_client(aws_access_key_id: str, aws_secret_access_key: str) -> s3.S3Client:
    """
    creates aws s3 client
    Args:
        aws_access_key_id: aws access key id for authentication
        aws_secret_access_key: aws access key secret for authentication

    Returns:
        S3Client instance
    """
    s3_client = s3.S3Client(aws_access_key_id, aws_secret_access_key)

    return s3_client


def get_mangle_yaan_config(myconf_file: str = None, workload_name: str = None) -> typing.Dict:
    """
    reads mangle-yaan config from myconf_file locally (if specified) or maxim-gun workload
    Args:
        myconf_file: mangle-yaan config file path (local)
        workload_name: workload name, required to read mangle-yaan config from maxim-gun

    Returns:

    """
    myconfig = None
    # read mangle-yaan config from command line
    if myconf_file is not None and myconf_file != "":
        conf_file = myconf_file
        mylog.debug("reading config locally from path={}".format(conf_file))
        myconfig = config_reader.parse_json(conf_file)

    # read mangle-yaan config from maxim-gun api (from maxim_gun.workload table)
    else:
        api_resource = mg_resources.MAXIMGUN.get("MANGLEYAAN_CONFIG")
        params = {"workload_name": workload_name}

        mylog.debug("reading config from maxim-gun app. resource={}".format(api_resource))
        response = mgclient.make_call(
            "GET", api_resource, retry_count=1, retry_sleep=5, params=params
        )
        if response.status_code == requests.codes.ok:
            myconfig = response.json.get("mangle_yaan_conf")
            # mylog.debug("maxim-gun api json response={}".format(res_json))
        else:
            mylog.error(
                "failed to read config from maxim-gun app. Request(resource={}, params={}). Response(status={}, text={})".format(
                    api_resource, params, response.status_code, response.text
                )
            )
            sys.exit(2)

    return myconfig


def setup_mangle_infra() -> None:
    """
    takes care of mangle infra setup e.g. CSP endpoint creation and connectivity with CSP K8S check
    """
    endpoint.create_and_test_mangle_endpoint(mclient)


def cleanup_old_reports(log_dir: str, max_count: int = 5) -> None:
    """
    deletes mangle-yaan-test-reports present under logs/ dir which are older than specified number of days
    Args:
        log_dir: log directory path
        max_count: maximum number of latest reports to keep

    Returns:
        None
    """
    mylog.info(
        "deleting older mangle-yaan-test-reports after keeping {} maximum reports".format(
            max_count
        )
    )

    my_report_path = myconfig.get("mangleYaan").get("testReportPath")
    my_report_name_expr = my_report_path.replace("logs/", "").replace("-{timeStamp}.html", "")

    # get list of files (file paths) starting with "mangle-yaan-test-report" and sort it by mtime in desc order
    fpaths = os.listdir(log_dir)
    fpaths = [
        os.path.join(log_dir, file_) for file_ in fpaths if file_.startswith(my_report_name_expr)
    ]
    fpaths = sorted(fpaths, key=os.path.getmtime, reverse=True)

    # keep max_count reports (latest) and delete remaining reports if any
    for fpath in fpaths[max_count:]:
        if os.path.exists(fpath) and os.path.isfile(fpath):
            try:
                os.remove(fpath)
            except OSError as fault:
                mylog.error("could not delete file {}. Exception={}".format(fpath, fault))


def prepare_setup(
    myconf_file: str = None,
    project_name: str = None,
    workload_name: str = None,
    run_id: str = None,
) -> None:
    """Performs setup preparation tasks i.e. ensuring network connectivity, reading mangle-yaan
    config file, initializing Mangle and CSP REST clients, creating Mangle endpoint credential
    and endpoint for CSP K8S cluster etc.

    Args:
      myconf_file: mangle-yaan configuration (json) file. If provided, It overrides default config file config/my.json
      project_name: project name created on maxim-gun UI
      workload_name: workload name created on maxim-gun UI
      run_id: run id received from maxim-gun

    Returns:
      None
    """
    check_network_availability()

    # creates maxim-gun REST client
    builtins.mgclient = create_maxim_gun_client()

    # update maxim-gun task status if run_id exists
    mg_agent.update_task(run_id, status=lib_params.MG_TASK_STATUS["STARTED"])

    # trigger a thread to update maxim-gun task periodically
    utils.start_mangleyaan_health_updater(run_id)

    # read mangle-yaan config and add it in builtins
    myconfig = get_mangle_yaan_config(myconf_file=myconf_file, workload_name=workload_name)
    if myconfig is None:
        mylog.error("failed to read mangle-yaan config file")
        sys.exit(2)
    builtins.myconfig = myconfig

    # creates mangle REST client
    builtins.mclient = create_mangle_client()

    # creates csp REST client
    builtins.cclient = create_csp_client()

    # creates csp kubernetes client
    csp_k8s_info = myconfig.get("k8sCluster")
    builtins.ckclient = create_csp_k8s_client(
        csp_k8s_info.get("kubeConfigFileName"), csp_k8s_info.get("namespace")
    )

    # create s3 client
    builtins.s3_client = create_s3_client(
        myconfig.get("aws").get("s3").get("awsAccessKeyID"),
        myconfig.get("aws").get("s3").get("awsSecretAccessKey"),
    )

    # creates mangle endpoint and confirms its connectivity
    setup_mangle_infra()

    # cleanup older mangle-yaan-test-reports
    cleanup_old_reports(lib_params.LOG_DIR, max_count=5)

    # test_runner cache to maintain states
    mycache = {}
    builtins.mycache = mycache

    # adding project_name and workload_name into mycache to use them in pytest-html report generation
    mycache["run_info"] = {}
    mycache["test_info"] = {}
    mycache["run_info"]["project_name"] = project_name
    mycache["run_info"]["workload_name"] = workload_name
    mycache["run_info"]["run_id"] = run_id

    mylog.info("setup is ready to run resiliency tests now")


def run_pytest(*args: str, run_id: str = None, **kwargs: str) -> int:
    # start_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    start_ts = datetime.datetime.now().strftime(lib_params.START_DATETIME_FORMAT)
    mycache["run_info"].update({"test_start_timestamp": start_ts})
    mylog.info("starting pytest test cases execution at: %s" % start_ts)

    # update maxim-gun task status if run_id exists
    mg_agent.update_task(run_id, status=lib_params.MG_TASK_STATUS["IN_PROGRESS"])

    status = pytest.main(*args, **kwargs)

    # end_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    end_ts = datetime.datetime.now().strftime(lib_params.END_DATETIME_FORMAT)
    mycache["run_info"].update({"test_end_timestamp": end_ts})
    mylog.info("pytest test cases execution finished at {} with status={}".format(end_ts, status))

    return status


def copy_results_and_logs(copy_results: bool = True, copy_logs: bool = True) -> str:
    """Tasks to be performed after pytest test-suites execution

    Args:
      copy_results: flag for enabling/disabling pytest test results copy on S3 bucket
      copy_logs: flag for enabling/disabling pytest test logs copy on S3 bucket

    Returns:
      s3 key (file-path) where file is copied
    """
    s3_conf = myconfig.get("aws").get("s3")
    if copy_logs:
        src_fpath = myconfig.get("mangleYaan").get("testLogPath")
        fname = os.path.basename(src_fpath)
        name, ext = os.path.splitext(fname)
        fname = "{name}-{timeStamp}{ext}".format(
            name=name, timeStamp=mycache["run_info"].get("test_start_timestamp"), ext=ext
        )
        s3_fpath = "{}{}".format(s3_conf.get("testLogPath"), fname)
        copy_file_on_s3(
            bucket_name=myconfig.get("aws").get("s3").get("bucketName"),
            src_fpath=src_fpath,
            s3_fpath=s3_fpath,
        )

    copy_results_status = None
    if copy_results:
        src_fpath = myconfig.get("mangleYaan").get("testReportPath")
        fname = os.path.basename(src_fpath)
        s3_fpath = "{}{}".format(s3_conf.get("testReportPath"), fname)
        copy_results_status = copy_file_on_s3(
            bucket_name=myconfig.get("aws").get("s3").get("bucketName"),
            src_fpath=src_fpath,
            s3_fpath=s3_fpath,
        )

    if copy_results_status:
        return s3_fpath

    return None


def copy_file_on_s3(bucket_name: str, src_fpath: str = None, s3_fpath: str = None) -> str:
    """copies file on S3 bucket

    Args:
      bucket_name: S3 bucket name
      src_fpath: file-path that need to be copied to S3 bucket
      s3_fpath: S3 file-path relative to S3 bucket bucket_name where src_fpath would be copied

    Returns:
        copy_status (True or False)
    """
    copy_status = False
    if src_fpath:
        s3_conf = myconfig.get("aws").get("s3")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=s3_conf.get("awsAccessKeyID"),
            aws_secret_access_key=s3_conf.get("awsSecretAccessKey"),
        )
        try:
            s3_client.upload_file(
                Filename=src_fpath, Bucket=bucket_name, Key=s3_fpath,
            )
            copy_status = True
            mylog.info("file {} successfully copied on s3 at {}".format(src_fpath, s3_fpath))
        except Exception as fault:
            mylog.error("file {} could not be copied on S3. Error={}".format(src_fpath, fault))
            mylog.exception(fault)
    else:
        mylog.debug("nothing to copy on S3")

    return copy_status


def generate_and_copy_result_trends(bucket: str, result_key: str, history_key: str) -> None:
    """generates and copies resiliency workloads result trends

    Args:
      bucket: S3 bucket name (e.g. csp-qe-res)
      result_key: resiliency workloads result trends s3 key (directory) in above bucket
      history_key: resiliency workloads result trends history s3 key (directory) in above bucket

    Returns:
        copy_status (True or False)
    """
    workload_history_key = (
        history_key.rstrip("/") + "/" + mycache["run_info"]["workload_name"] + "/" + "history"
    )
    workload_history_backup_key = (
        history_key.rstrip("/")
        + "/"
        + mycache["run_info"]["workload_name"]
        + "/"
        + "backup-history"
    )

    allure_raw = lib_params.ALLURE_LOG_DIR + os.path.sep + "raw"
    allure_html = lib_params.ALLURE_LOG_DIR + os.path.sep + "html"
    allure_raw_history = lib_params.ALLURE_LOG_DIR + os.path.sep + "raw" + os.path.sep + "history"
    allure_html_history = (
        lib_params.ALLURE_LOG_DIR + os.path.sep + "html" + os.path.sep + "history"
    )

    if s3_client.if_key_exists(bucket, workload_history_key):
        s3_client.download_files_from_s3(bucket, workload_history_key, allure_raw)

    allure_report_gen_cmd = "allure generate {} --clean -o {}".format(allure_raw, allure_html)
    # allure_report_gen_cmd = b'allure generate /Users/mtarun/vmware/code/mangle-yaan-service/logs/allure/raw --clean ' \
    #                         b'-o /Users/mtarun/vmware/code/mangle-yaan-service/logs/allure/html'
    cmd_output = utils.run_cmd(allure_report_gen_cmd)
    mylog.debug("cmd='{}' executed with output={}".format(allure_report_gen_cmd, cmd_output))

    if cmd_output.startswith(b"Report successfully generated to"):
        mylog.debug("allure report generated successfully")

        if s3_client.if_key_exists(bucket, workload_history_key):
            if s3_client.if_key_exists(bucket, workload_history_backup_key):
                mylog.debug(
                    "deleting workload history backup key={}".format(workload_history_backup_key)
                )
                s3_client.delete_files_from_s3(bucket, workload_history_backup_key)

            mylog.debug(
                "creating a backup for workload history-key={} to history-backup-key={}".format(
                    workload_history_key, workload_history_backup_key
                )
            )
            s3_client.copy_files_on_s3_from_src_key(
                bucket, workload_history_key, workload_history_backup_key
            )

            mylog.debug("deleting workload history key={}".format(workload_history_key))
            s3_client.delete_files_from_s3(bucket, workload_history_key)
        mylog.debug(
            "uploading allure html history dir {} to s3 workload history {}".format(
                allure_html_history, workload_history_key
            )
        )
        s3_client.upload_files_to_s3(
            bucket, os.path.dirname(workload_history_key), allure_html_history
        )

        if s3_client.if_key_exists(bucket, result_key):
            mylog.debug("deleting result key={}".format(result_key))
            s3_client.delete_files_from_s3(bucket, result_key)
        mylog.debug(
            "uploading allure html dir {} to s3 workload results {}".format(
                allure_html, result_key
            )
        )
        s3_client.upload_files_to_s3(
            bucket, result_key, allure_html, skip_parent_dir_creation=True
        )


def get_test_modules_from_testsuite_names(testsuite_names: str) -> typing.List[str]:
    """verifies test-suites exist in testsuites_info.json and returns corresponding test-module file-paths.
    test-suites are a bit user-friendly names. They are mapped with test-modules in testsuites_info.json file.

    Note: All test-modules should have an mapping (test-suite->test-module) in testsuites_info.json file.

    Args:
      testsuite_names: comma separated list of test_suite names

    Returns:
      testmodule_paths: list of test-module paths
    """
    testsuites_info_file = lib_params.TESTLIB_DIR + os.path.sep + "testsuites_info.json"
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
    testsuites_info_file = lib_params.TESTLIB_DIR + os.path.sep + "testsuites_info.json"
    testsuites_info = config_reader.parse_json(testsuites_info_file)

    testsuite_names = pprint.pformat(list(testsuites_info.keys()))
    print("Available testsuites are:\n{}\n".format(testsuite_names))


def main() -> None:
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
        default="",
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
        "--run_id",
        action="store",
        type=str,
        default="",
        help="run_id of the job triggered at Maxim-Gun",
    )
    parser.add_argument(
        "--list_testsuite_names", action="store_true", help="list of available testsuites",
    )
    parser.add_argument(
        "--skip_copy_logs", action="store_true", help="skip logs copy on s3",
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

    if args.myconfig is not None:
        # removes leading and trailing single/double quotes, white-spaces from args.pytest_args
        args.myconfig = args.myconfig.strip()
        args.myconfig = args.myconfig.strip("'")
        args.myconfig = args.myconfig.strip('"')

    if args.run_id is not None:
        # removes leading and trailing single/double quotes, white-spaces from args.pytest_args
        args.run_id = args.run_id.strip()
        args.run_id = args.run_id.strip("'")
        args.run_id = args.run_id.strip('"')

    prepare_setup(
        myconf_file=args.myconfig,
        project_name=args.project_name,
        workload_name=args.workload_name,
        run_id=args.run_id,
    )

    pytest_status = run_pytest(pytest_cmdline, run_id=args.run_id)
    # don't copy logs to S3 for pytest usage error. seems incorrect --pytest_args are passed. Also, update task status as FAILED

    copy_results = True
    copy_result_trends = True
    end_time = datetime.datetime.now().strftime(lib_params.MG_DATETIME_FORMAT)
    if pytest_status == 4:
        copy_results = False
        copy_result_trends = False
        mg_agent.update_task(
            args.run_id, status=lib_params.MG_TASK_STATUS["FAILED"], end_time=end_time
        )
        # sys.exit(3)
    if pytest_status == 2:
        mylog.error("Pytest execution terminated by user")
        copy_results = False
        copy_result_trends = False
        mg_agent.update_task(args.run_id, end_time=end_time)
        # sys.exit(3)

    if args.skip_copy_logs:
        copy_results = False
        copy_result_trends = False

    if copy_result_trends:
        generate_and_copy_result_trends(
            myconfig.get("aws").get("s3").get("resultTrendsBucketName"),
            mycache["run_info"]["workload_name"],
            myconfig.get("aws").get("s3").get("resultTrendsHistoryPath"),
        )

    if copy_results:
        s3_path = copy_results_and_logs(copy_results=copy_results)
        mg_agent.update_task(
            args.run_id,
            status=lib_params.MG_TASK_STATUS["COMPLETED"],
            end_time=end_time,
            report_url=s3_path,
            result=mycache["run_info"]["result_summary"]["aggregatd_result"],
        )
        mg_agent.update_result(
            args.run_id, end_time=end_time, report_details=mycache["run_info"]["result_summary"]
        )


if __name__ == "__main__":
    try:
        main()
    finally:
        # stops thread to update maxim-gun task periodically
        utils.stop_mangleyaan_health_updater()
