#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" REST client interface """

__author__ = "tarun mudgal"

import abc
import logging
import time
import typing

import requests
import urllib3

from lib import params
from lib.common import utils

requests.packages.urllib3.disable_warnings()


# logging.getLogger("urllib3").setLevel(logging.WARNING)


class RESTClient(abc.ABC):
    """
        This class prepares REST calls, send requests and handle errors
    """

    def __init__(
        self, scheme="https://", host="", port=443, api_prefix="", ssl_verify=False, timeout=None
    ):
        self._base_url = scheme + host + ":" + str(port) + api_prefix
        self._ssl_verify = ssl_verify
        self._timeout = timeout

        self._headers = None
        if not self._ssl_verify:
            urllib3.disable_warnings()

    # def __repr__(self):
    #     return "RESTClient(host={}, api_prefix={}, ssl_verify={}, timeout={}, session={})".format(
    #         self.__host, self.__api_prefix, self.__ssl_verify, self.__timeout, self.__session
    #     )

    @abc.abstractmethod
    def init_session(self):
        pass

    @abc.abstractmethod
    def init_session_without_retry(self):
        pass

    # @utils.log_args
    def request(
        self,
        method: str,
        api_resource: str,
        retry_count: int = 1,
        retry_sleep: int = 5,
        disable_implicit_retry: bool = False,
        **kwargs: str,
    ) -> typing.NewType("Response", requests.Response):
        """sends HTTP request for RESTClient

        Args:
          method: request verb e.g. GET, POST, PUT, DELETE etc.
          api_resource: api resource of the client
          retry_count: maxium number of retries allowed
          retry_sleep: sleep (in seconds) in between retries
          disable_implicit_retry: if set to True, self._session_no_retry is used that doesn't use
                                    requests.packages.urllib3.util.retry.Retry

        Returns:
          requests.Response
        """

        session_obj = None
        url = self._base_url + api_resource

        # sets session_obj with either self._session (with implicit retries) or
        # self._session_no_retry (without implicit retries)
        if not disable_implicit_retry:
            session_obj = self._session
        else:
            session_obj = self._session_no_retry

        # sets headers, timeout etc. with defaults if not provided in request
        if self._headers is not None:
            if kwargs.get("headers") is not None:
                kwargs["headers"].update(self._headers)
            else:
                kwargs["headers"] = {}
                kwargs["headers"].update(self._headers)

        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self._timeout

        if retry_count < 0:
            retry_count = 0

        # attempts to make explict retries as per retry_count provided
        attempt = 0
        while attempt < retry_count + 1:
            try:
                attempt += 1
                mylog.debug(
                    "RESTClient: Sending a request with method={}, resource={}, disable_implicit_retry={}".format(
                        method, api_resource, disable_implicit_retry
                    )
                )

                response = session_obj.request(method, url, **kwargs)
                mylog.debug(
                    "RESTClient: request with method={}, resource={} succeeded in ({}) attempt(s)".format(
                        method, api_resource, attempt
                    )
                )
                return response
            except params.HTTP_RETRIABLE_ERRORS as fault:
                mylog.debug(
                    "RESTClient: Failed to send request due to connection error. method={}, resource={}, error={}".format(
                        method, api_resource, fault
                    )
                )
                if attempt < retry_count + 1:
                    mylog.debug(
                        "RESTClient: retry({}) after {} seconds".format(attempt, retry_sleep)
                    )
                    time.sleep(retry_sleep)
                else:
                    mylog.exception(fault)
                    raise
            except Exception as fault:
                mylog.debug(
                    "RESTClient: Exception occurred in method={}, url={}".format(method, url)
                )
                mylog.exception(fault)
                raise


def request(
    method: str, url: str, retry_count: int = 1, retry_sleep: int = 5, **kwargs: str
) -> requests.Response:
    """thin wrapper over requests.request API with retry logic implemented
    Args:
      method: request verb e.g. GET, POST, PUT, DELETE etc.
      url: request url including api resource
      retry_count: maxium number of retries allowed
      retry_sleep: sleep (in seconds) in between retries

    Returns:
      requests.Response
    """
    if retry_count < 0:
        retry_count = 0

    attempt = 0
    while attempt < retry_count + 1:
        try:
            attempt += 1
            mylog.debug(
                "Sending a request with method=%s, url=%s", method, url,
            )
            response = requests.request(method, url, **kwargs)
            mylog.debug(
                "Request with method={}, url={} succeeded in ({}) attempt(s)".format(
                    method, url, attempt
                )
            )
            return response
        except params.HTTP_RETRIABLE_ERRORS as fault:
            mylog.debug(
                "Failed to send request due to connection error. method={}, url={}, error={}".format(
                    method, url, fault
                )
            )
            if attempt < retry_count + 1:
                mylog.debug("retry({}) after {} seconds".format(attempt, retry_sleep))
                time.sleep(retry_sleep)
            else:
                mylog.exception(fault)
                raise
        except Exception as fault:
            mylog.debug("Exception occurred in method={}, url={}".format(method, url))
            mylog.exception(fault)
            raise
