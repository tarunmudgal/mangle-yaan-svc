#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import requests

from lib.common import utils
from lib.common.rest_client import RESTClient
from lib.csp import resources


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
        self, host, api_prefix, refresh_token, ssl_verify=False, timeout=None,
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
                "could not fetch access_token using url={}, headers={}, payload={}".format(
                    access_token_url, headers, payload
                )
            )
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
