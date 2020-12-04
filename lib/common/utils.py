#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" utility functions """

__author__ = "tarun mudgal"

import datetime
import functools
import logging
import sys
import threading
import time
from pprint import pprint

import boto3
from dateutil.tz import tzutc

from lib import params
from lib.maximgun import agent as mg_agent

MY_HEALTH_UPDATE_EVENT_HANDLER = threading.Event()


def log_args(func):
    @functools.wraps(func)
    def _log_args(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = ["{}={}".format(k, v) for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        mylog.debug("func {}({}) called".format(func.__name__, signature))
        return func(*args, **kwargs)

    return _log_args


def verify_status(do_log=True, return_status=True, success_status_range=(200, 299)):
    def _verify_response(func):
        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = ["{}={}".format(k, v) for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            response = func(*args, **kwargs)

            status = False
            if success_status_range[0] <= response.status_code <= success_status_range[1]:
                if do_log:
                    mylog.debug("func {}({}) status: PASS".format(func.__name__, signature))
                status = True
            else:
                if do_log:
                    mylog.error("func {}({}) status: FAIL".format(func.__name__, signature))
                    mylog.debug("response: {}".format(response))
            if return_status:
                return status, response
            return response

        return func_wrapper

    return _verify_response


def purge_old_reports_from_s3(
    aws_key="AKIAUE4JITGQ3LKSAK5E",
    aws_secret="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",
    bucket_name="csp-e2e-qe",
    s3_key_prefix="mangle-yaan/results/mangle-yaan-test-report",
    days_before=60,
):
    s3_client = boto3.client("s3", aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,)
    report_objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_key_prefix)
    # pprint(report_objects["Contents"])

    cur_time = datetime.datetime.now(tz=tzutc())
    for rp_obj in report_objects["Contents"]:
        datetime_diff = cur_time - rp_obj["LastModified"]
        if datetime_diff.days > days_before:
            try:
                print("deleting file {} from bucket {}".format(rp_obj["Key"], bucket_name))
                s3_client.delete_object(Bucket=bucket_name, Key=rp_obj["Key"])
            except Exception as fault:
                print(
                    "file {} could not be deleted from bucket {}. Error={}".format(
                        rp_obj["Key"], bucket_name, fault
                    )
                )


def get_mangleyaan_passing_test_percent(result_summary: dict) -> float:
    total_tests = result_summary["passed"] + result_summary["failed"] + result_summary["skipped"]
    return (result_summary["passed"] / total_tests) * 100


def get_mangleyaan_result_status(pass_percent: float) -> str:
    if params.MANGLEYAAN_PASS_THRESHOLD <= pass_percent:
        return params.MANGLEYAAN_AGGREGATED_RESULT["PASS"]
    elif (
        params.MANGLEYAAN_PARTIALLY_PASS_THRESHOLD
        <= pass_percent
        < params.MANGLEYAAN_PASS_THRESHOLD
    ):
        return params.MANGLEYAAN_AGGREGATED_RESULT["PARTIAL_PASS"]
    else:
        return params.MANGLEYAAN_AGGREGATED_RESULT["FAIL"]


def start_mangleyaan_health_updater(run_id: str):
    global MY_HEALTH_UPDATE_EVENT_HANDLER

    mylog.info("initializing health updater thread...")
    if run_id:
        MY_HEALTH_UPDATE_EVENT_HANDLER.set()
        th_job = threading.Thread(
            target=_update_health, args=(run_id, MY_HEALTH_UPDATE_EVENT_HANDLER)
        )
        th_job.start()
    else:
        mylog.error(
            "failed to initialize health updater theread due to invalid run_id. Ignore if execution is running locally"
        )


def stop_mangleyaan_health_updater():
    global MY_HEALTH_UPDATE_EVENT_HANDLER

    mylog.info("terminating health updater thread...")
    MY_HEALTH_UPDATE_EVENT_HANDLER.clear()


def _update_health(run_id: str, event: threading.Event):
    while event.is_set():
        try:
            time.sleep(params.MANGLEYAAN_TASK_UPDATE_INTERVAL)
            mylog.debug("updating end_time for run_id={}".format(run_id))
            mg_agent.update_task(
                run_id, end_time=datetime.datetime.now().strftime(params.MG_DATETIME_FORMAT)
            )
        except Exception as fault:
            mylog.error("Exception occurred while updating maxim-gun task")
            mylog.exception(fault)


if __name__ == "__main__":
    purge_old_reports_from_s3(days_before=30)
