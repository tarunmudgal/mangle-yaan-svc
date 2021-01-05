#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import requests

from lib.maximgun import resources as mg_resources


def update_task(
    run_id: str,
    end_time: str = None,
    status: str = None,
    report_url: str = None,
    cancel: int = None,
    result: str = None,
) -> bool:
    """
    updates maxim-gun task status (maxim_gun.run_test table)
    Args:
        run_id: task run id received from maxim-gun
        end_time: task end time
        status: status to be updated. Valid entries are 'Started', 'Running', 'Completed', 'Failed', 'Cancelled'
        report_url: test report url which is copied on s3
        result: aggregated result of the task. Valid entries are PASS, FAIL, PARTIALLY-PASS
        cancel: flag to set if task is failed. Valid entries are 0, 1
    Returns:
        status
    """
    if run_id:
        update_task_info = {}
        get_task_api_resource = mg_resources.MAXIMGUN.get("GET_TASK_DETAILS").format(run_id=run_id)
        get_task_response = mgclient.make_call("GET", get_task_api_resource)
        if get_task_response.status_code == requests.codes.ok:
            task_info = get_task_response.json.get("result")[0]
            update_task_info["run_id"] = run_id
            update_task_info["end_time"] = end_time if end_time else task_info["end_time"]
            update_task_info["status"] = status if status else task_info["status"]
            update_task_info["report_url"] = report_url if report_url else task_info["report_url"]
            update_task_info["result"] = result if result else task_info["baseline_result"]
            update_task_info["cancel"] = cancel if cancel else 0  # task_info["cancel"]
        else:
            mylog.error(
                "failed to fetch maxim-gun task details for run_id={}. Cannot update task.".format(
                    run_id
                )
            )
            return False

        api_resource = mg_resources.MAXIMGUN.get("TASK_STATUS_UPDATE")
        response = mgclient.make_call("POST", api_resource, json=update_task_info)
        if response.status_code == requests.codes.ok:
            mylog.info("maxim-gun job run_id={} updated successfully".format(run_id))
        else:
            mylog.error(
                "failed to update maxim-gun job run_id={} where end_time={}, status={}, report_url={}, cancel={}".format(
                    run_id, end_time, status, report_url, cancel
                )
            )
    else:
        mylog.error("invalid run_id found. Ignore if execution is running locally")


def update_result(run_id: str, end_time: str = None, report_details: any = None) -> bool:
    if run_id:
        update_result_info = {}
        update_result_info["run_id"] = run_id
        update_result_info["time"] = end_time
        update_result_info["report_details"] = [
            {
                "PASS": report_details["passed"],
                "FAIL": report_details["failed"],
                "SKIP": report_details["skipped"],
            }
        ]
        api_resources = mg_resources.MAXIMGUN["POST_RESULT_DETAIL"]
        print(update_result_info)
        response = mgclient.make_call("POST", api_resources, json=update_result_info)
        if response.status_code == requests.codes.ok:
            mylog.info("maxim-gun job run result updated successfully")
