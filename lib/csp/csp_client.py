#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Mangle REST Client """

import typing

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lib import params
from lib.common import rest_client, utils
from lib.csp import resources

# http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html
DEFAULT_RETRY_OBJ = Retry(
    total=params.CCLIENT_MAX_RETRIES,
    status_forcelist=params.CCLIENT_STATUS_FORCELIST,
    method_whitelist=params.CCLIENT_METHOD_WHITELIST,
    backoff_factor=params.CCLIENT_BACKOFF_FACTOR,
)


class CSPResponse(object):
    """CSPClient Response Wrapper"""

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
        return "CSPResponse(url={} status_code={} headers={} json={} text={})".format(
            self.url, self.status_code, self.headers, self.json, self.text
        )


class CSPClient(rest_client.RESTClient):
    """
    CSPClient (HTTP Client) that interacts with CSP REST APIs
    """

    __single_instance = None

    def __init__(
        self,
        host: str,
        refresh_token: str,
        api_prefix: str = resources.API_PREFIX,
        scheme: str = "https://",
        retry_obj: Retry = DEFAULT_RETRY_OBJ,
        ssl_verify: bool = False,
        timeout: int = None,
    ) -> None:
        """Initializes singleton CSPClient that is used to make CSP API calls
        Args:
            host: CSP hostname
            refresh_token: CSP refresh token that is used to fetch access token
            api_prefix: CSP API Prefix
            scheme: it should be either 'http://' or 'https://'
            retry_obj: requests.packages.urllib3.util.retry.Retry object used to enable retries on specific status_code(s)
            ssl_verify: True if SSL needs to be enabled else False
            timeout: maximum time to wait (for connect and read) before raising Timeout exception
        Raises:
            None
        Returns:
            CSPClient object
        """

        adapter = HTTPAdapter(max_retries=retry_obj)

        if CSPClient.__single_instance is not None:
            raise Exception("CSPClient is a singleton class and cannot have more than one objects")

        CSPClient.__single_instance = self

        super().__init__(
            scheme=scheme, host=host, api_prefix=api_prefix, ssl_verify=ssl_verify, timeout=timeout
        )

        self._refresh_token = refresh_token
        self._session = requests.Session()
        self._session.mount(scheme, adapter)
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
        # response = requests.request("POST", access_token_url, headers=headers, data=payload)
        response = rest_client.request(
            "POST", access_token_url, retry_count=1, retry_sleep=5, headers=headers, data=payload
        )

        if response.status_code == requests.codes.ok:
            return response.json().get("access_token")
        else:
            raise Exception(
                "could not fetch access_token using Request(url={}, headers={}, payload={}). Response(status={}, text={})".format(
                    access_token_url, headers, payload, response.status_code, response.text
                )
            )

    # @utils.log_args
    def make_call(
        self, verb: str, api_resource: str, **kwargs: str
    ) -> CSPResponse:
        """
        makes a HTTP call using RESTClient.request API
        Args:
            verb: request verb e.g. GET, POST, PUT, DELETE etc.
            api_resource: api resource handle
            kwargs: kwargs that are supported by requests.request. In addition, retry_count and retry_sleep are also supported
        Returns:
            CSPResponse obj
        """
        req_resp = self.request(verb, api_resource, **kwargs)
        if req_resp.status_code == 401:
            mylog.debug("Authorization error occurred for CSP API call. Updating access_token")
            self.init_session()
            req_resp = self.request(verb, api_resource, **kwargs)
        return CSPResponse(req_resp)
