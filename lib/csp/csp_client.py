#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import functools
import time
import abc
import requests

from lib.common import utils
from lib.csp import resources
from lib import params

import urllib3


class CSPResponse(object):
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
        return "CSPResponse(url={} status_code={} headers={} json={} text={})".format(
            self.url, self.status_code, self.headers, self.json, self.text
        )


class RESTClient(abc.ABC):
    """
        This class prepares REST calls, send requests and handle errors
    """

    def __init__(self, host, port=443, api_prefix='', ssl_verify=False, timeout=None):
        self._scheme = 'https://'
        self._base_url = self._scheme + host + ':' + str(port) + api_prefix
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

    @utils.log_args
    def request(self, method, api_resource, retry_count=1, retry_sleep=5, **kwargs):
        """
            Send requests, handles errors and retry requests for connection
            and timeout errors.
        """
        url = self._base_url + api_resource

        if self._headers is not None:
            if kwargs.get('headers') is not None:
                kwargs['headers'].update(self._headers)
            else:
                kwargs['headers'] = {}
                kwargs['headers'].update(self._headers)

        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self._timeout

        if retry_count < 0:
            retry_count = 0

        attempt = 0
        while attempt < retry_count + 1:
            try:
                attempt += 1
                response = self._session.request(method, url, **kwargs)
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


class CSPClient(RESTClient):
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
            api_prefix,
            refresh_token,
            ssl_verify=False,
            timeout=None,
    ):
        """Init Mangle API with hostname and login credentials."""

        if CSPClient.__single_instance is not None:
            raise Exception("CSPClient is a singleton class and cannot have more than one objects")

        CSPClient.__single_instance = self

        super().__init__(host, api_prefix=api_prefix, ssl_verify=ssl_verify, timeout=timeout)

        self._refresh_token = refresh_token
        self._session = requests.Session()
        self.init_session()

        mylog.debug("CSPClient obj %s initialized." % self)

    def __repr__(self):
        return "CSPClient(base_url={})".format(self._base_url)

    def init_session(self):
        self._access_token = self.get_access_token()

        self._session.headers = {"csp-auth-token": self._access_token}
        self._session.verify = self._ssl_verify

    def get_access_token(self):
        access_token_url = self._base_url + resources.AM.get("AUTHORIZE")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = "refresh_token={}".format(self._refresh_token)

        mylog.debug("fetching access_token for CSP API calls")
        response = requests.request("POST", access_token_url, headers=headers, data=payload)

        if response.status_code == requests.codes.ok:
            return response.json().get("access_token")
        else:
            mylog.exception(
                "could not fetch access_token using url={}, headers={}, payload={}".format(access_token_url, headers,
                                                                                           payload))
            raise

    # @utils.log_args
    def make_call(self, verb, api_resource, **kwargs):
        """
        # TODO
        """
        req_resp = self.request(verb, api_resource, **kwargs)
        if req_resp.status_code == 401:
            mylog.debug("Authorization error occurred for CSP API call. Updating access_token")
            self.init_session()
            req_resp = self.request(verb, api_resource, **kwargs)
        return CSPResponse(req_resp)
