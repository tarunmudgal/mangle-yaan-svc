#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import argparse
import datetime
import logging
import os
import sched
import sys
import time

import requests

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASEDIR)

PROJECTDIR = os.path.dirname(BASEDIR)
RESULTSDIR = os.path.join(PROJECTDIR, "results")
MAXIM_GUN_ENDPOINT = "http://maxim-gun-service.svc-stage.eng.company.com"
MANGLE_YAAN_TEST_REPORT_NAME = "mangle-yaan-test-report.html"

START = 0
# No of Iterations (1hr - 360 polls with duration of 10 seconds)
RETRIES = 360


def get_logger(logger_name):
    log = logging.getLogger(logger_name)
    logging.basicConfig(
        format="%(asctime)s: %(name)s :%(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log.setLevel(logging.DEBUG)
    return log


logger = get_logger("res_tests")


def run_test(workload_name, project_name):
    run_api_endpoint = MAXIM_GUN_ENDPOINT + "/api/res/runtest/mangle-yaan/run"
    config_api_endpoint = MAXIM_GUN_ENDPOINT + "/api/res/runtest/mangle-yaan/config"
    workload_info_api_endpoint = MAXIM_GUN_ENDPOINT + "/api/workload/info"

    # data to be sent to api
    dt = datetime.datetime.now()

    # sending post request and saving response as response object
    workload_config = requests.get(
        url=config_api_endpoint,
        params={"workload_name": workload_name},
        headers={"Content-Type": "application/json"},
    ).json()

    workload_info = requests.get(
        url=workload_info_api_endpoint,
        params={"workload_name": workload_name},
        headers={"Content-Type": "application/json"},
    ).json()

    # Format datetime string
    x = dt.strftime("%d-%m-%Y %H:%M:%S")
    tag = "Run via Jenkins on " + x
    data = {
        "workload_id": workload_info.get("workload_id"),
        "testsuite_names": workload_config.get("workload_testsuites"),
        "tag": tag,
        "version": "0",
    }
    print(data)

    # sending post request and saving response as response object
    r = requests.post(
        url=run_api_endpoint, json=data, headers={"Content-Type": "application/json"}
    )

    output = r.json()
    rid = str(output["run_id"])
    logger.info("Started Test with id " + rid)
    return rid


def status(run_id):
    api_endpoint = MAXIM_GUN_ENDPOINT + "/api/history/status?run_id=" + str(run_id)
    r = requests.get(url=api_endpoint, headers={"Content-Type": "application/json"})
    output = r.json()
    st = output["status"]
    if st == "Completed":
        return True
    else:
        return False


def download(run_id):
    api_endpoint = (
        MAXIM_GUN_ENDPOINT + "/api/res/history/download-html-report?run_id=" + str(run_id)
    )
    r = requests.get(url=api_endpoint, headers={"Content-Type": "application/json"})
    report_path = (
        RESULTSDIR + os.path.sep + "TestReports" + os.path.sep + MANGLE_YAAN_TEST_REPORT_NAME
    )
    with open(report_path, "wb") as test_report:
        test_report.write(r.content)


def check_status(sc, run_id):
    global START
    logger.info("Test with id " + str(run_id) + " is still running...")
    if not status(run_id):
        sc.enter(10, 1, check_status, (sc, run_id))
        if START <= RETRIES:
            START += 1
        else:
            headers = {"content-type": "application/json"}
            # csp-lambda-watch webhook url
            csp_webhookurl = (
                "https://hooks.slack.com/services/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"
            )
            # cspqe-non-func-notifs webhook url
            cspqe_webhookurl = (
                "https://hooks.slack.com/services/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"
            )
            try:
                data = " CSP Resiliency Tests failed in preview \n *Jenkins Build:* {build_url}".format(
                    build_url=str(os.getenv("BUILD_URL")) + "Gatling_20Results/"
                )
                enrich_data = {"text": data}
                logger.info("posting to #csp-lamda-watch")
                requests.post(url=csp_webhookurl, json=enrich_data, headers=headers)
                logger.info("posting to #cspqe-non-func-notifs")
                # requests.post(url=cspqe_webhookurl, json=enrich_data, headers=headers)
            except Exception as e:
                logger.exception(e)
                logger.error(
                    "Failed while posting slack notification - {exception}".format(exception=e)
                )
            exit(1)

    elif status(run_id):
        download(run_id)


if __name__ == "__main__":
    logger.info("----------- Starting e2e resiliency tests -----------")
    parser = argparse.ArgumentParser(description="Trigger e2e resiliency tests")

    parser.add_argument("--workload_name", "-workload_name", required=True, help="Workload_id")

    parser.add_argument("--project_name", "-project_name", required=True, help="Workload_id")

    sc = sched.scheduler(time.time, time.sleep)
    input_args = parser.parse_args()
    run_id = run_test(input_args.workload_name, input_args.project_name)
    sc.enter(10, 1, check_status, (sc, run_id))
    sc.run()
