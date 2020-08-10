#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import functools

from lib.common import rest_client, utils
from lib.mangle import resources


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
            self, host, username, password, api_prefix=resources.API_PREFIX, ssl_verify=False, timeout=None,
    ):
        """Init Mangle API with hostname and login credentials."""

        if MangleClient.__single_instance is not None:
            raise Exception("MangleApi is a singleton class and cannot have more than one objects")

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
        return "MangleAPI(%r, %r, %r, %r)" % (
            self.host,
            self.username,
            self.password,
            self.api_prefix,
        )

    def init_rest_client(self):
        self.mangle_base_url = "https://{host}/{prefix}".format(host=self.host, prefix=self.api_prefix)
        self.rest_client = rest_client.RESTClient(self.username, self.password, ssl_verify=self.ssl_verify,
                                                  timeout=self.timeout)

    @utils.log_args
    def make_call(self, verb, api_resource, **kwargs):
        """
        # TODO
        """
        request_url = self.mangle_base_url + '/' + api_resource
        req_resp = self.rest_client.request(verb, request_url, **kwargs)

        return MangleResponse(req_resp)
