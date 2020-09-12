#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = 'tarun mudgal'

import requests
from lib.maximgun import resources as mg_resources


def update_task(run_id: str, cancel: int = 0, end_time: str = "", status: str = "", report_url: str = "") -> None:
    """
    updates maxim-gun task status (maxim_gun.run_test table)
    Args:
        run_id: task run id received from maxim-gun
        cancel:
        end_time: task finish end time
        status:
        report_url:

    Returns:

    """
    if run_id:
        api_resource = mg_resources.MAXIMGUN.get("TASK_STATUS_UPDATE")
        request_body = {
            "run_id": run_id,
            "cancel": cancel,
            "end_time": end_time,
            "status": status,
            "report_url": report_url
        }
        response = mgclient.make_call(
            "POST", api_resource, json=request_body
        )
        if response.status_code == requests.codes.ok:
            mylog.info("maxim-gun job run_id={} updated".format(run_id))
        else:
            mylog.error(
                "failed to update maxim-gun job run_id={} where cancel={}, end_time={}, status={}, report_url={}".format(
                    run_id, cancel, end_time, status, report_url))
    else:
        mylog.error("invalid run_id found. Ignore if running locally")