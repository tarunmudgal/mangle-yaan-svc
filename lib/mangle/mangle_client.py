#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import functools
import time

import requests

from lib.common import rest_client, utils
from lib.mangle import resources
from lib import params


class MangleResponse(object):
    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
        self.headers = response.headers
        self.json = None
        self.text = None
        try:
            self.json = response.json()
        except ValueError as fault:
            self.content = response.text

    def __repr__(self):
        return "MangleResponse(url={} status_code={} headers={} json={} text={})".format(
            self.url, self.status_code, self.headers, self.json, self.text
        )


class MangleClient(object):
    """
    Wrapper to interact with the Mangle REST API's

    Parameters
    ----------
    host: string
        IP Address or FQDN to Mangle
    username: string
        Mangle username
    password: string
        Mangle password
    api_prefix: string
        API prefix (will be append to the hostname)
    ssl_verify: bool, optional
        Perform SSL host verification (default=False)
    """

    __single_instance = None

    def __init__(
            self,
            host,
            username,
            password,
            api_prefix=resources.API_PREFIX,
            ssl_verify=False,
            timeout=None,
    ):
        """Init Mangle API with hostname and login credentials."""

        if MangleClient.__single_instance is not None:
            raise Exception("MangleClient is a singleton class and cannot have more than one objects")

        MangleClient.__single_instance = self

        self.host = host
        self.username = username
        self.password = password
        self.api_prefix = api_prefix
        self.ssl_verify = ssl_verify
        self.timeout = timeout
        self.init_rest_client()

        mylog.debug("MangleClient obj %s initialized." % self)

    def __repr__(self):
        return (
            "MangleClient(host={}, username={}, password={}, api_prefix={}, ssl_verify={} timeout={})".format(
                self.host,
                self.username,
                self.password,
                self.api_prefix,
                self.ssl_verify,
                self.timeout,
            )
        )

    def init_rest_client(self):
        self.mangle_base_url = "https://{host}{prefix}".format(
            host=self.host, prefix=self.api_prefix
        )
        self.rest_client = rest_client.RESTClient(
            self.username, self.password, ssl_verify=self.ssl_verify, timeout=self.timeout
        )

    # @utils.log_args
    def make_call(self, verb, api_resource, **kwargs):
        """
        # TODO
        """
        request_url = self.mangle_base_url + api_resource
        req_resp = self.rest_client.request(verb, request_url, **kwargs)

        return MangleResponse(req_resp)

    # @utils.log_args
    def trigger_fault_task_and_wait_for_completion(self, verb, api_resource, retry_count=12, retry_duration=5,
                                                   **kwargs):
        """
        # TODO
        """
        t_id = ""
        t_status = ""
        _retry = 0
        request_url = self.mangle_base_url + api_resource
        req_resp = self.rest_client.request(verb, request_url, **kwargs)
        req_resp = MangleResponse(req_resp)
        time.sleep(60)  # give some time to Mangle to create task
        if req_resp.status_code == requests.codes.ok:
            t_id = req_resp.json.get("id")
            task_url = self.mangle_base_url + resources.TASK_CTRLR["TASKS"] + "/" + t_id
            task_resp = self.rest_client.request('GET', task_url)
            task_resp = MangleResponse(task_resp)
            if task_resp.status_code == requests.codes.ok:
                while _retry < retry_count:
                    if task_resp.json.get("mangleTaskInfo").get("taskStatus") == params.MANGLE_TASK_STATUS["COMPLETED"]:
                        mylog.debug("task id={} is completed successfully".format(req_resp.json.get("id")))
                        return t_id, params.MANGLE_TASK_STATUS["COMPLETED"]
                    elif task_resp.json.get("mangleTaskInfo").get("taskStatus") == params.MANGLE_TASK_STATUS["FAILED"]:
                        mylog.error("task id={} is failed".format(req_resp.json.get("id")))
                        return t_id, params.MANGLE_TASK_STATUS["FAILED"]
                    elif task_resp.json.get("mangleTaskInfo").get("taskStatus") == params.MANGLE_TASK_STATUS[
                        "IN_PROGRESS"]:
                        mylog.debug(
                            "task id={} is in progress. will retry after {} secs".format(req_resp.json.get("id"),
                                                                                         retry_duration))
                        t_status = params.MANGLE_TASK_STATUS["IN_PROGRESS"]
                    elif task_resp.json.get("mangleTaskInfo").get("taskStatus") == params.MANGLE_TASK_STATUS[
                        "NOT_STARTED"]:
                        mylog.debug(
                            "task id={} is not started yet. will retry after {} secs".format(req_resp.json.get("id"),
                                                                                             retry_duration))
                        t_status = params.MANGLE_TASK_STATUS["NOT_STARTED"]
                    time.sleep(retry_duration)
                    _retry += 1
                    task_resp = self.rest_client.request('GET', task_url)
                    task_resp = MangleResponse(task_resp)
            else:
                mylog.error("could not fetch details for task id={}".format(req_resp.json.get("id")))
                t_status = "TASK_NOT_FETCHED"
        else:
            t_status = "TASK_NOT_TRIGGERED"
            mylog.error("could not trigger fault task ".format(req_resp))

        return t_id, t_status
