#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import typing

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lib import params
from lib.common import rest_client, utils
from lib.maximgun import resources

# http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html
DEFAULT_RETRY_OBJ = Retry(
    total=params.MGCLIENT_MAX_RETRIES,
    status_forcelist=params.MGCLIENT_STATUS_FORCELIST,
    method_whitelist=params.MGCLIENT_METHOD_WHITELIST,
    backoff_factor=params.MGCLIENT_BACKOFF_FACTOR,
)


class MGResponse:
    """MGClient Response Wrapper"""

    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
        self.headers = response.headers
        self.json = None
        self.text = None
        try:
            self.json = response.json()
        except ValueError as fault:
            mylog.exception(fault)
        finally:
            self.text = response.text

    def __repr__(self):
        return "MGResponse(url={} status_code={} headers={} json={} text={})".format(
            self.url, self.status_code, self.headers, self.json, self.text
        )


class MGClient(rest_client.RESTClient):
    """
    MGClient (HTTP Client) that interacts with CSP REST APIs
    """

    __single_instance = None

    def __init__(
        self,
        host: str,
        api_prefix: str = resources.MAXIMGUN_RES_API_PREFIX,
        scheme: str = "https://",
        retry_obj: Retry = DEFAULT_RETRY_OBJ,
        ssl_verify: bool = False,
        timeout: int = None,
    ) -> None:
        """Initializes singleton MGClient that is used to make MaximGun API calls
        Args:
            host: MaximGun hostname
            api_prefix: MaximGun API Prefix
            scheme: it should be either 'http://' or 'https://'
            retry_obj: requests.packages.urllib3.util.retry.Retry object used to enable retries on specific status_code(s)
            ssl_verify: True if SSL needs to be enabled else False
            timeout: maximum time to wait (for connect and read) before raising Timeout exception
        Raises:
            None
        Returns:
            MGClient object
        """

        if MGClient.__single_instance is not None:
            raise Exception("MGClient is a singleton class and cannot have more than one objects")

        MGClient.__single_instance = self

        super().__init__(
            scheme=scheme, host=host, api_prefix=api_prefix, ssl_verify=ssl_verify, timeout=timeout
        )

        self._scheme = scheme
        self._retry_obj = retry_obj
        self.init_session(self._scheme, self._retry_obj)
        self.init_session_without_retry()

        mylog.debug("MGClient obj %s initialized." % self)

    def __repr__(self):
        return "MGClient(base_url={})".format(self._base_url)

    def init_session(self, scheme, retry_obj):
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_obj)
        self._session.mount(scheme, adapter)
        self._session.verify = self._ssl_verify

    def init_session_without_retry(self):
        self._session_no_retry = requests.Session()
        self._session_no_retry.verify = self._ssl_verify

    # @utils.log_args
    def make_call(self, verb: str, api_resource: str, **kwargs: str) -> MGResponse:
        """
        makes a HTTP call using RESTClient.request API
        Args:
            verb: request verb e.g. GET, POST, PUT, DELETE etc.
            api_resource: api resource handle
            kwargs: kwargs that are supported by requests.request. In addition, retry_count and retry_sleep are also supported
        Returns:
            MGResponse obj
        """
        req_resp = self.request(verb, api_resource, **kwargs)

        return MGResponse(req_resp)
