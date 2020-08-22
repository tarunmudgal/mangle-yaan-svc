#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" resiliency test runner """

__author__ = "tarun mudgal"

import builtins
import datetime
import inspect
import os
import sys

import boto3
import pytest
import requests

from lib.common import config_reader, logger
from lib.csp import csp_client
from lib.csp import resources as csp_resources
from lib.mangle import endpoint, mangle_client

requests.packages.urllib3.disable_warnings()

# constants initialization
ROOT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
builtins.ROOT_DIR = ROOT_DIR

LOG_DIR = ROOT_DIR + os.path.sep + "logs"
CONF_DIR = ROOT_DIR + os.path.sep + "config"

if not os.path.exists(LOG_DIR):
    print("creating log directory: %s" % LOG_DIR, flush=True)
    os.makedirs(LOG_DIR)

# mylog = logger.Log(logger.get_logger())
mylog = logger.get_logger()
builtins.mylog = mylog
mylog.info("logger initialized")


def check_network_availability(
        request_url="https://www.google.com", resp_code_exp=requests.codes.ok
):
    try:
        resp = requests.get(request_url, verify=False)
        assert resp.status_code == resp_code_exp
        mylog.info("Network Availability Check: OK")
    except Exception as fault:
        mylog.error("Network Availability Check: Failed")
        mylog.error("Error: %s. Exiting %s" % (fault, sys.argv[0]))
        sys.exit(1)


def prepare_setup():
    check_network_availability()

    # read mangle-yaan config (my.json). Looks up in environment vars if set else pick-up the default value
    conf_file = os.getenv("MYCONFIG", CONF_DIR + os.path.sep + "my.json")
    mylog.debug("reading config file from path={}".format(conf_file))
    myconfig = config_reader.parse_config(conf_file)
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
        csp_resources.API_PREFIX,
        csp_conf.get("defaultUser").get("refreshToken"),
        ssl_verify=False,
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

    mylog.info("setup is ready to run resiliency tests now")


def run_pytest(*args, **kwargs):
    # start_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    start_ts = datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S.%f")
    mycache.update({"test_start_timestamp": start_ts})
    mylog.info("starting pytest test cases execution at: %s" % start_ts)

    pytest.main(*args, **kwargs)

    # end_ts = datetime.datetime.now().strftime("%d/%m/%Y, %I:%M:%S.%f %p")
    end_ts = datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S.%f")
    mycache.update({"test_start_timestamp": end_ts})
    mylog.info("pytest test cases execution finished at: %s" % end_ts)


def post_run_activities():
    # import pdb; pdb.set_trace()
    copied_successfully, failed_to_copy = copy_files_on_s3(
        bucket_name=myconfig.get("aws").get("s3").get("bucketName"),
        file_paths=[myconfig.get("mangleYaan").get("testReportPath")],
    )
    if failed_to_copy:
        mylog.error("test reports = {} could not be copied over S3".format(failed_to_copy))
    else:
        mylog.info("test reports = {} copied successfully over S3".format(copied_successfully))


def copy_files_on_s3(bucket_name, file_paths=None):
    if file_paths:
        s3_conf = myconfig.get("aws").get("s3")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=s3_conf.get("awsAccessKeyID"),
            aws_secret_access_key=s3_conf.get("awsSecretAccessKey"),
        )

        copied_successfully = []
        failed_to_copy = []
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

        return copied_successfully, failed_to_copy

    mylog.debug("nothing to copy on S3")


if __name__ == "__main__":
    # import pdb;
    # pdb.set_trace()
    prepare_setup()
    run_pytest(sys.argv[1:])
    post_run_activities()
