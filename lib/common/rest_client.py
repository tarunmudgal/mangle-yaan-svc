#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" REST client interface """

__author__ = "tarun mudgal"

import logging
import time

import requests
import urllib3
from requests.auth import HTTPBasicAuth

from lib import params
from lib.common import utils

requests.packages.urllib3.disable_warnings()
logging.getLogger("urllib3").setLevel(logging.WARNING)


class RESTClient(object):
    """
        This class prepares REST calls, send requests and handle errors
    """

    def __init__(self, username, password, ssl_verify=False, timeout=None):
        self.__username = username
        self.__password = password
        self.__ssl_verify = ssl_verify
        self.__timeout = timeout
        self.init_session()
        if not ssl_verify:
            urllib3.disable_warnings()

    def __repr__(self):
        return "RESTClient(username={}, password={}, ssl_verify={}, timeout={}, session={})".format(
            self.__username, self.__password, self.__ssl_verify, self.__timeout, self.__session
        )

    def init_session(self):
        self.__session = requests.Session()
        self.__session.auth = HTTPBasicAuth(self.__username, self.__password)
        self.__session.verify = self.__ssl_verify

    @utils.log_args
    def request(self, method, url, retry_count=1, retry_sleep=5, **kwargs):
        """
            Send requests, handles errors and retry requests for connection
            and timeout errors.
        """

        if kwargs.get("headers") is None:
            kwargs["headers"] = {"Content-type": "application/json"}
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.__timeout

        if retry_count < 0:
            retry_count = 0

        attempt = 0
        while attempt < retry_count + 1:
            try:
                attempt += 1
                response = self.__session.request(method, url, **kwargs)
                return response
            except params.HTTP_RETRIABLE_ERRORS as fault:
                mylog.debug(
                    "RESTClient: Failed to send request due to connection error. method=%s, url=%s, error=%s",
                    method,
                    url,
                    fault
                )
                if attempt < retry_count + 1:
                    mylog.debug("RESTClient: retry(%d) after %d seconds", attempt, retry_sleep)
                    time.sleep(retry_sleep)
                else:
                    mylog.exception(fault)
                    raise
            except Exception as fault:
                mylog.debug("RESTClient: Exception occurred in method=%s, url=%s", method, url)
                mylog.exception(fault)
                raise
