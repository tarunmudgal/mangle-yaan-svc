#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CSP REST Client (standalone) for different use-cases"""

import abc
import inspect
import logging.handlers
import os
import sys
import time
import typing

import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.exceptions import (ConnectTimeout, ConnectionError, ReadTimeout, SSLError, Timeout)
from requests.packages.urllib3.exceptions import ConnectTimeoutError
from requests.packages.urllib3.util.retry import Retry

requests.packages.urllib3.disable_warnings()


# define constants
HTTP_RETRIABLE_ERRORS = (
    ConnectionError,
    ConnectTimeout,
    ConnectTimeoutError,
    ReadTimeout,
    SSLError,
    Timeout,
)
# http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html
DEFAULT_RETRY_OBJ = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE", ],
    backoff_factor=1,
)
CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOGFILE_PATH = CURRENT_DIR + os.path.sep + "csp_client_standalone.log"
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"


# initialize logger
mylog = logging.getLogger("csp_client_standalone")
mylog.setLevel(logging.DEBUG)

file_handler = logging.handlers.RotatingFileHandler(
    LOGFILE_PATH, maxBytes=10_000_000, backupCount=10,
)
if (
        os.path.isfile(LOGFILE_PATH)
        and os.path.getsize(LOGFILE_PATH) > 0
        # and sys.platform != "win32"
):
    file_handler.doRollover()  # Recycle log name: .1 -> .2, ..., .max_logs

console_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
formatter.converter = time.gmtime  # log UTC timestamps
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
console_handler.flush = sys.stdout.flush

mylog.addHandler(console_handler)
mylog.addHandler(file_handler)


# core methods that can be consumed in different use cases
def rest_request(
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
                "Request with method=%s, url=%s succeeded in (%d) attempt(s)",
                method,
                url,
                attempt,
            )
            return response
        except HTTP_RETRIABLE_ERRORS as fault:
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


class RESTClient(abc.ABC):
    """
    This class prepares REST calls, send requests and handle errors
    """

    def __init__(
            self, scheme="https://", host="", port=443, api_prefix="", ssl_verify=False, timeout=None,
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
            except HTTP_RETRIABLE_ERRORS as fault:
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


class CSPResponse:
    """CSPClient Response Wrapper"""

    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
        self.resp_time = response.elapsed.total_seconds()
        self.headers = response.headers
        self.json = None
        self.text = None
        try:
            self.json = response.json()
        except ValueError as fault:
            self.text = response.text

    def __repr__(self):
        return "CSPResponse(url={} status_code={} resp_time={}(seconds) headers={} json={} text={})".format(
            self.url, self.status_code, self.resp_time, self.headers, self.json, self.text
        )


class CSPClient(RESTClient):
    """
    CSPClient (HTTP Client) that interacts with CSP REST APIs
    """

    __single_instance = None

    def __init__(
            self,
            host: str,
            refresh_token: str,
            api_prefix: str = "/csp/gateway",
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
            scheme=scheme,
            host=host,
            api_prefix=api_prefix,
            ssl_verify=ssl_verify,
            timeout=timeout,
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
        access_token_url = self._base_url + "/am/api/auth/api-tokens/authorize"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "visid_incap_1729671=8nN6ObgUQO2DZgaqE39n1MjxK18AAAAAQUIPAAAAAAAB8r3FWv5IQSDtqQiSFWMy; nlbi_1729671=GGBSOJWSxhwQTi/AcPvC0AAAAAAMzj+SD4kv+gKLfKspMsW7; incap_ses_1135_1729671=cVzfZWfL9GDzPfgmnVTAD5owYl8AAAAAPnB6wFOkTMNOoJ/uPACH4g==; incap_ses_711_1729671=Iw6xVjF0ohoa4Zw/3PrdCRt1aF8AAAAADpUs5iu2LEcjkWuXCzxFuA==; incap_ses_1132_1729671=ZHs4bdSuDATLlV6OI6y1D0/6aF8AAAAAsQh8diZEML1Ro1a0bL1fvA==",
        }
        payload = "refresh_token={}".format(self._refresh_token)

        mylog.debug("fetching access_token for CSP API calls")
        # response = requests.request("POST", access_token_url, headers=headers, data=payload)
        response = rest_request(
            "POST", access_token_url, retry_count=1, retry_sleep=5, headers=headers, data=payload,
        )

        if response.status_code == requests.codes.ok:
            return response.json().get("access_token")
        else:
            raise Exception(
                "could not fetch access_token using Request(url={}, headers={}, payload={}). Response(status={}, text={})".format(
                    access_token_url, headers, payload, response.status_code, response.text,
                )
            )

    # @utils.log_args
    def make_call(self, verb: str, api_resource: str, **kwargs: str) -> CSPResponse:
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


if __name__ == "__main__":

    # define constants for current use case
    SERVICE_ID = "142cd4ab-5727-4e7d-9cc2-a87ff8998635"
    ORGS_FILE_PATH = "OrgList.txt"

    ORG_RESOURCE = "/am/api/orgs/{orgId}"
    ORG_ACCESS_RESOURCE = "/slc/api/definitions/external/{serviceId}/org-access/actions"
    SERVICE_ACCESS_RESOURCE = "/slc/api/service-access"
    SUBSCRIPTION_RESOURCE = "/commerce/api/v3/subscriptions"

    # initialize csp rest client
    cclient = CSPClient(
        "console-preview.cloud.vmware.com",
        "cMtNzVdi8mLwfFR2bllMLtgVLSWo7QfJV5TegQlM0R-KYf7z5SHPCjC7Y4I7bCDT",
        timeout=120,
    )

    # use case: remove service access from given orgs
    with open(ORGS_FILE_PATH) as fp:
        for org_id in fp:
            org_id = org_id.strip()

            mylog.info("processing org_id={}".format(org_id))

            # Get list of subscriptions in an org
            get_subscriptions_resp = cclient.make_call(
                "GET",
                SUBSCRIPTION_RESOURCE,
                params={"orgId": org_id}
            )
            mylog.info("get_subscriptions_resp={}".format(get_subscriptions_resp))

            # Perform important verifications before processing further for a given org_id
            if get_subscriptions_resp.status_code != 200:
                mylog.error(
                    "Error occurred for POST {} for org={}".format(SUBSCRIPTION_RESOURCE, org_id)
                )
                mylog.info("skipping processing org_id={} as get subscriptions call failed".format(org_id))
                continue
            else:
                if get_subscriptions_resp.json.get("totalResults") > 0:
                    mylog.error(
                        "active subscriptions observed for org_id={}. Therefore, skipping processing for this org")
                    continue

            # Set DENY_ACCESS for a service in an org
            org_access_resp = cclient.make_call(
                "POST",
                ORG_ACCESS_RESOURCE.format(serviceId=SERVICE_ID),
                params={"action": "DENY_ACCESS"},
                json={"orgId": org_id},
            )
            # mylog.info("org_access_resp={}".format(org_access_resp))
            if org_access_resp.status_code != 202:
                mylog.error(
                    "Error occurred for POST {} for org={}".format(ORG_ACCESS_RESOURCE, org_id)
                )

            # Delete service access from an org
            delete_service_access_resp = cclient.make_call(
                "DELETE",
                SERVICE_ACCESS_RESOURCE,
                json={"orgId": org_id, "serviceDefinitionId": SERVICE_ID},
            )
            # mylog.info("service_access_resp={}".format(delete_service_access_resp))
            if delete_service_access_resp.status_code != 200:
                mylog.error(
                    "Error occurred for DELETE {} for org={}".format(
                        SERVICE_ACCESS_RESOURCE, org_id
                    )
                )

            # Add service access to an org
            # ToDo: this call is for testing purpose and should be removed later
            add_service_access_resp = cclient.make_call(
                "POST",
                SERVICE_ACCESS_RESOURCE,
                json={"orgId": org_id, "serviceDefinitionId": SERVICE_ID, "isTosPreSigned": True},
            )
            # mylog.info("add_service_access_resp={}".format(add_service_access_resp))
            if add_service_access_resp.status_code != 202:
                mylog.error(
                    "Error occurred for POST {} for org={}\n".format(
                        SERVICE_ACCESS_RESOURCE, org_id
                    )
                )
