#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" resiliency test runner """

__author__ = "tarun mudgal"

import argparse
import builtins
import datetime
import inspect
import os
import shlex
import subprocess
import sys

import pytest
import requests

from lib.common import config_reader, logger
from lib.mangle import mangle_client, endpoint

requests.packages.urllib3.disable_warnings()

ROOT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
builtins.ROOT_DIR = ROOT_DIR

LOG_DIR = ROOT_DIR + os.path.sep + "logs"
CONF_DIR = ROOT_DIR + os.path.sep + "config"

if not os.path.exists(LOG_DIR):
    print("creating log directory: %s" % LOG_DIR, flush=True)
    os.makedirs(LOG_DIR)

mylog = logger.Log(logger.get_logger())
builtins.mylog = mylog
mylog.info("logger initialized")


def check_arg(args=None):
    parser = argparse.ArgumentParser(description="resiliency test runner")
    parser.add_argument("-t", "--type", help="type", required="True", default="pre")
    parser.add_argument("-p", "--project_name", help="project name", required="True", default="")
    parser.add_argument("-w", "--workload_name", help="workload name", required="True", default="")
    parser.add_argument("-r", "--run_id", help="run_id", required="True", default="")

    results = parser.parse_args(args)
    return (results.type, results.project_name, results.workload_name, results.run_id)


def run_command(command):
    print("\n-------------\nRunning...." + command)
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc


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

    # read mangle-yaan config (my.json)
    conf_file = CONF_DIR + os.path.sep + "my.json"
    myconfig = config_reader.parse_config(conf_file)
    builtins.myconfig = myconfig

    mangle_conf = myconfig.get("mangle")
    myclient = mangle_client.MangleClient(
        mangle_conf.get("host"),
        mangle_conf.get("username"),
        mangle_conf.get("password"),
        timeout=120,
    )

    ep_cred = endpoint.EndpointCredential(myclient)
    status, response = ep_cred.create_credential_k8s_cluster(myconfig.get('k8sCluster').get('credentialName'),
                                                             myconfig.get('k8sCluster').get('kubeConfigFileName'))
    if not status:
        mylog.error("Failed to create k8s cluster credential for credentialName={}, kubeConfigFileName={}".format(
            myconfig.get('k8sCluster').get('credentialName'),
            myconfig.get('k8sCluster').get('kubeConfigFileName')))
        sys.exit(2)
    mylog.info(
        "credential '{}' for k8s cluster created successfully".format(myconfig.get('k8sCluster').get('credentialName')))

    ep = endpoint.Endpoint(myclient)
    status, response = ep.create_endpoint_k8s_cluster(myconfig.get('k8sCluster').get('endpointName'),
                                                      myconfig.get('k8sCluster').get('credentialName'),
                                                      myconfig.get('k8sCluster').get('namespace'))
    if not status:
        mylog.error("Failed to create k8s cluster endpoint for endpointName={}, credentialName={}, namespace={}".format(
            myconfig.get('k8sCluster').get('endpointName'),
            myconfig.get('k8sCluster').get('credentialName'),
            myconfig.get('k8sCluster').get('namespace')))
        sys.exit(2)
    mylog.info(
        "endpoint '{}' for k8s cluster created successfully".format(myconfig.get('k8sCluster').get('endpointName')))

    mylog.info("setup is ready to run resiliency tests now")


def run_pytest():
    suite_start_time = datetime.datetime.now()
    start_stamp = "%s%02d%02d %02d:%02d:%02d,%03d" % (
        suite_start_time.year,
        suite_start_time.month,
        suite_start_time.day,
        suite_start_time.hour,
        suite_start_time.minute,
        suite_start_time.second,
        int(str(suite_start_time.microsecond)[:3]),
    )
    mylog.info("starting test cases execution at %s time" % start_stamp)


if __name__ == "__main__":
    import pdb;pdb.set_trace()
    prepare_setup()
    # pytest.main(sys.argv[1:])
