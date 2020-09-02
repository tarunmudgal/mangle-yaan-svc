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

    # @utils.log_args
    def request(
        self,
        method: str,
        api_resource: str,
        retry_count: int = 1,
        retry_sleep: int = 5,
        **kwargs: str,
    ) -> typing.NewType("Response", requests.Response):
        """sends HTTP request for RESTClient

        Args:
          method: request verb e.g. GET, POST, PUT, DELETE etc.
          api_resource: api resource of the client
          retry_count: maxium number of retries allowed
          retry_sleep: sleep (in seconds) in between retries

        Returns:
          requests.Response
        """
        url = self._base_url + api_resource

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

        attempt = 0
        while attempt < retry_count + 1:
            try:
                attempt += 1
                mylog.debug(
                    "RESTClient: Sending a request with method=%s, resource=%s",
                    method,
                    api_resource,
                )

                response = self._session.request(method, url, **kwargs)
                mylog.debug(
                    "RESTClient: request with method=%s, resource=%s succeeded in (%d) attempt(s)",
                    method,
                    api_resource,
                    attempt,
                )
                return response
            except params.HTTP_RETRIABLE_ERRORS as fault:
                mylog.debug(
                    "RESTClient: Failed to send request due to connection error. method=%s, resource=%s, error=%s",
                    method,
                    api_resource,
                    fault,
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
                "Request with method=%s, url=%s succeeded in (%d) attempt(s)", method, url, attempt
            )
            return response
        except params.HTTP_RETRIABLE_ERRORS as fault:
            mylog.debug(
                "Failed to send request due to connection error. method=%s, url=%s, error=%s",
                method,
                url,
                fault,
            )
            if attempt < retry_count + 1:
                mylog.debug("retry(%d) after %d seconds", attempt, retry_sleep)
                time.sleep(retry_sleep)
            else:
                mylog.exception(fault)
                raise
        except Exception as fault:
            mylog.debug("Exception occurred in method=%s, url=%s", method, url)
            mylog.exception(fault)
            raise
