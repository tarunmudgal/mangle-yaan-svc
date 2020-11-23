#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import base64
import time
import typing

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lib import params
from lib.common import utils
from lib.common.rest_client import RESTClient
from lib.mangle import resources

# http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html
DEFAULT_RETRY_OBJ = Retry(
    total=params.MCLIENT_MAX_RETRIES,
    status_forcelist=params.MCLIENT_STATUS_FORCELIST,
    method_whitelist=params.MCLIENT_METHOD_WHITELIST,
    backoff_factor=params.MCLIENT_BACKOFF_FACTOR,
)


class MangleResponse:
    """MangleClient Response Wrapper"""

    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
        self.headers = response.headers
        self.json = None
        self.text = None
        try:
            self.json = response.json()
        except ValueError as fault:
            self.text = response.text

    def __repr__(self):
        return "MangleResponse(url={} status_code={} headers={} json={} text={})".format(
            self.url, self.status_code, self.headers, self.json, self.text
        )


class MangleClient(RESTClient):
    """
    MangleClient (HTTP Client) that interacts with Mangle REST APIs
    """

    __single_instance = None

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        api_prefix: str = resources.API_PREFIX,
        scheme: str = "https://",
        retry_obj: Retry = DEFAULT_RETRY_OBJ,
        ssl_verify: bool = False,
        timeout: int = None,
    ) -> None:
        """Initializes singleton MangleClient that is used to make Mangle API calls
        Args:
            host: Mangle service hostname
            username: Mangle user-name
            password: Mangle password
            api_prefix: Mangle API Prefix
            scheme: it should be either 'http://' or 'https://'
            retry_obj: requests.packages.urllib3.util.retry.Retry object used to enable retries on specific status_code(s)
            ssl_verify: True if SSL needs to be enabled else False
            timeout: maximum time to wait (for connect and read) before raising Timeout exception
        Raises:
            None
        Returns:
            MangleClient object
        """

        if MangleClient.__single_instance is not None:
            raise Exception(
                "MangleClient is a singleton class and cannot have more than one objects"
            )

        MangleClient.__single_instance = self

        super().__init__(host=host, api_prefix=api_prefix, ssl_verify=ssl_verify, timeout=timeout)

        self._scheme = scheme
        self._retry_obj = retry_obj
        self._user = username
        self._passwd = password
        self.init_session(self._scheme, self._retry_obj)
        self.init_session_without_retry()

        mylog.debug("MangleClient obj %s initialized." % self)

    def __repr__(self):
        return "MangleClient(base_url={})".format(self._base_url)

    def init_session(self, scheme, retry_obj):
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_obj)
        self._session.mount(scheme, adapter)
        user_pass_bytes = "{}:{}".format(self._user, self._passwd).encode()
        b64e_val = base64.b64encode(user_pass_bytes).decode()
        self._session.headers = {"Authorization": "Basic {}".format(b64e_val)}
        self._session.verify = self._ssl_verify

    def init_session_without_retry(self):
        self._session_no_retry = requests.Session()
        user_pass_bytes = "{}:{}".format(self._user, self._passwd).encode()
        b64e_val = base64.b64encode(user_pass_bytes).decode()
        self._session_no_retry.headers = {"Authorization": "Basic {}".format(b64e_val)}
        self._session_no_retry.verify = self._ssl_verify

    # @utils.log_args
    def make_call(self, verb: str, api_resource: str, **kwargs: str) -> MangleResponse:
        """
        makes a HTTP call using RESTClient.request API
        Args:
            verb: request verb e.g. GET, POST, PUT, DELETE etc.
            api_resource: api resource handle
            kwargs: kwargs that are supported by requests.request. In addition, retry_count and retry_sleep are also supported
        Returns:
            MangleResponse obj
        """
        req_resp = self.request(verb, api_resource, **kwargs)

        return MangleResponse(req_resp)

    # @utils.log_args
    def trigger_fault_task_and_wait_for_completion(
        self,
        verb: str,
        api_resource: str,
        retry_count: int = 12,
        retry_duration: int = 5,
        **kwargs: str,
    ) -> typing.Tuple[int, str]:
        """
        # TODO
        """
        t_id = ""
        t_status = ""
        _retry = 0
        req_resp = self.request(verb, api_resource, **kwargs)
        req_resp = MangleResponse(req_resp)
        time.sleep(60)  # give some time to Mangle to create task
        if req_resp.status_code == requests.codes.ok:
            t_id = req_resp.json.get("id")
            task_res = resources.TASK_CTRLR["TASKS"] + "/" + t_id
            task_resp = self.request("GET", task_res)
            task_resp = MangleResponse(task_resp)
            if task_resp.status_code == requests.codes.ok:
                while _retry < retry_count:
                    if (
                        task_resp.json.get("mangleTaskInfo").get("taskStatus")
                        == params.MANGLE_TASK_STATUS["COMPLETED"]
                    ):
                        mylog.debug(
                            "task id={} is completed successfully".format(req_resp.json.get("id"))
                        )
                        return t_id, params.MANGLE_TASK_STATUS["COMPLETED"]
                    elif (
                        task_resp.json.get("mangleTaskInfo").get("taskStatus")
                        == params.MANGLE_TASK_STATUS["FAILED"]
                    ):
                        mylog.error("task id={} is failed".format(req_resp.json.get("id")))
                        return t_id, params.MANGLE_TASK_STATUS["FAILED"]
                    elif (
                        task_resp.json.get("mangleTaskInfo").get("taskStatus")
                        == params.MANGLE_TASK_STATUS["IN_PROGRESS"]
                    ):
                        mylog.debug(
                            "task id={} is in progress. will retry after {} secs".format(
                                req_resp.json.get("id"), retry_duration
                            )
                        )
                        t_status = params.MANGLE_TASK_STATUS["IN_PROGRESS"]
                    elif (
                        task_resp.json.get("mangleTaskInfo").get("taskStatus")
                        == params.MANGLE_TASK_STATUS["NOT_STARTED"]
                    ):
                        mylog.debug(
                            "task id={} is not started yet. will retry after {} secs".format(
                                req_resp.json.get("id"), retry_duration
                            )
                        )
                        t_status = params.MANGLE_TASK_STATUS["NOT_STARTED"]
                    time.sleep(retry_duration)
                    _retry += 1
                    task_resp = self.request("GET", task_res)
                    task_resp = MangleResponse(task_resp)
            else:
                mylog.error(
                    "could not fetch details for task id={}. Response={}".format(
                        req_resp.json.get("id"), task_resp
                    )
                )
                t_status = "TASK_NOT_FETCHED"
        else:
            t_status = "TASK_NOT_TRIGGERED"
            mylog.error("could not trigger fault task. Response={}".format(req_resp))

        return t_id, t_status
