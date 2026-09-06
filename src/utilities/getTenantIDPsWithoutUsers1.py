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
import pprint

import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.exceptions import (ConnectTimeout, ConnectionError, ReadTimeout, SSLError, Timeout)
from requests.packages.urllib3.exceptions import ConnectTimeoutError
from requests.packages.urllib3.util.retry import Retry

import config

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
LOGFILE_PATH = CURRENT_DIR + os.path.sep + "csp_client_get_org_owners.log"
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"

# initialize logger
mylog = logging.getLogger("csp_client_get_orgs")
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
                # mylog.debug(
                #     "RESTClient: Sending a request with method=%s, resource=%s",
                #     method,
                #     api_resource,
                # )

                response = self._session.request(method, url, **kwargs)
                # mylog.debug(
                #     "RESTClient: request with method=%s, resource=%s succeeded in (%d) attempt(s)",
                #     method,
                #     api_resource,
                #     attempt,
                # )
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

    def divide_chunks(l, n):

        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]


if __name__ == "__main__":
    # define constants for current use case
    SERVICE_ID = "142cd4ab-5727-4e7d-9cc2-a87ff8998635"
    ORGS_FILE_PATH = "orgList_trap_domain_orgs.txt"

    IDP_REGISTRATIONS = "/am/api/idp-registrations"
    USER_SEARCH = "/am/api/v2/users/search"
    IDP_TENANT_DELETE = "/am/api/idp-registrations/{idp_registrations_id}?force=true"

    # initialize csp rest client
    cclient = CSPClient(
        "console-preview.cloud.company.com",
        config.REFRESH_TOKEN,
        timeout=120,
    )

    # making call for each user block
    mylog.info("Test started")

    idp_tenants_with_no_users = [
        {'idpId': '97fe8763-aba9-4f91-9141-0a30547a2606', 'idpDisplayName': 'ASTRA-OKTA-JITAKK7Rjit-idp',
         'idpDomain': 'perf232.com', 'totalUsers': 0},
        {'idpId': 'bac19abc-a829-4205-83a6-6feed8ae0a1b', 'idpDisplayName': 'ASTRA-OKTA-JIT96YYYjit-idp',
         'idpDomain': 'perf408.com', 'totalUsers': 0},
        {'idpId': '6225b5a7-2ad7-476c-9db6-b8c39e1839b1', 'idpDisplayName': 'ASTRA-OKTA-JITMI2LFjit-idp',
         'idpDomain': 'perf429.com', 'totalUsers': 0},
        {'idpId': 'f305d3ad-fcda-4676-9c4b-7cdaddafc62c', 'idpDisplayName': 'ASTRA-OKTA-JITF15Y4jit-idp',
         'idpDomain': 'perf8.com', 'totalUsers': 0},
        {'idpId': '43932789-e78f-49b7-95ae-63c3e1696150', 'idpDisplayName': 'ASTRA-OKTA-JITE3YU4jit-idp',
         'idpDomain': 'perf411.com', 'totalUsers': 0},
        {'idpId': '7af75a12-ba49-4ca8-a81e-a7b9a640b110', 'idpDisplayName': 'ASTRA-OKTA-JITGUA5Hjit-idp',
         'idpDomain': 'perf31.com', 'totalUsers': 0},
        {'idpId': '9050153c-7689-4c5e-9de4-9e2ae1630c89', 'idpDisplayName': 'ASTRA-OKTA-JITM36QCjit-idp',
         'idpDomain': 'perf409.com', 'totalUsers': 0},
        {'idpId': '06f4de52-babe-4cef-85d3-41eb3a79e170', 'idpDisplayName': 'ASTRA-OKTA-JITAIJUUjit-idp',
         'idpDomain': 'perf48.com', 'totalUsers': 0},
        {'idpId': '56527d96-adfe-4e49-8318-92c59698f316', 'idpDisplayName': 'ASTRA-OKTA-JITBU4U0jit-idp',
         'idpDomain': 'perf418.com', 'totalUsers': 0},
        {'idpId': '1cfaed12-a520-412b-bb9a-5aad8f419e21', 'idpDisplayName': 'ASTRA-OKTA-JITLK8TMjit-idp',
         'idpDomain': 'perf159.com', 'totalUsers': 0},
        {'idpId': '34602163-6286-460c-99aa-625bbb5cfeeb', 'idpDisplayName': 'ASTRA-OKTA-JITXUM4Ujit-idp',
         'idpDomain': 'perf397.com', 'totalUsers': 0},
        {'idpId': '8c126287-fb3c-4b67-b6fc-13a3c1b870f4', 'idpDisplayName': 'ASTRA-OKTA-JITEP0B1jit-idp',
         'idpDomain': 'perf13.com', 'totalUsers': 0},
        {'idpId': '0861089a-6f21-4eee-aefa-045018faf491', 'idpDisplayName': 'ASTRA-OKTA-JITIW09Fjit-idp',
         'idpDomain': 'perf276.com', 'totalUsers': 0},
        {'idpId': '885a2edc-e54d-45c8-a1ab-8423573d498b', 'idpDisplayName': 'ASTRA-OKTA-JITX219Djit-idp',
         'idpDomain': 'perf363.com', 'totalUsers': 0},
        {'idpId': 'e03ffb97-7b55-42bb-937f-1c89741c2a74', 'idpDisplayName': 'ASTRA-OKTA-JIT8RZBDjit-idp',
         'idpDomain': 'perf291.com', 'totalUsers': 0},
        {'idpId': 'defe1953-a503-4970-8d02-7fab81e550e3', 'idpDisplayName': 'ASTRA-OKTA-JIT9J526jit-idp',
         'idpDomain': 'perf412.com', 'totalUsers': 0},
        {'idpId': 'a183a074-39b7-44ca-a68b-baf927f8f79a', 'idpDisplayName': 'ASTRA-OKTA-JITLNJK7jit-idp',
         'idpDomain': 'perf144.com', 'totalUsers': 0},
        {'idpId': 'bc5a59a5-da1f-445d-84a1-49c95476d0bb', 'idpDisplayName': 'ASTRA-OKTA-JIT21S1Ajit-idp',
         'idpDomain': 'perf242.com', 'totalUsers': 0},
        {'idpId': 'fb335960-3330-40eb-84c5-cffcc8081997', 'idpDisplayName': 'ASTRA-OKTA-JIT5DM6Pjit-idp',
         'idpDomain': 'perf283.com', 'totalUsers': 0},
        {'idpId': '4450d78c-e78f-48cb-9a70-b23fafaeaa5a', 'idpDisplayName': 'ASTRA-OKTA-JITU1TTCjit-idp',
         'idpDomain': 'perf141.com', 'totalUsers': 0},
        {'idpId': '63400a17-a6d3-4f49-bf97-988f00ffb5b9', 'idpDisplayName': 'ASTRA-OKTA-JITIAG84jit-idp',
         'idpDomain': 'perf41.com', 'totalUsers': 0},
        {'idpId': 'de24528e-0672-4b1d-9f52-2bd56ec69331', 'idpDisplayName': 'ASTRA-OKTA-JITTB9YMjit-idp',
         'idpDomain': 'perf223.com', 'totalUsers': 0},
        {'idpId': 'decb4860-ae3a-478e-a934-1f044654c355', 'idpDisplayName': 'ASTRA-OKTA-JITL35NNjit-idp',
         'idpDomain': 'perf91.com', 'totalUsers': 0},
        {'idpId': 'e6500e96-c453-422b-9c13-165c4b449386', 'idpDisplayName': 'ASTRA-OKTA-JITXIBVCjit-idp',
         'idpDomain': 'perf471.com', 'totalUsers': 0},
        {'idpId': '2528d39b-18cb-4dfa-a18f-c086940fff23', 'idpDisplayName': 'ASTRA-OKTA-JIT8Q60Sjit-idp',
         'idpDomain': 'perf270.com', 'totalUsers': 0},
        {'idpId': '388b9049-4af2-4ee0-9437-8bc81131402c', 'idpDisplayName': 'ASTRA-OKTA-JITUYY5Djit-idp',
         'idpDomain': 'perf160.com', 'totalUsers': 0},
        {'idpId': '39add843-ff20-49e0-930d-a6c0c044382f', 'idpDisplayName': 'ASTRA-OKTA-JITBBNW0jit-idp',
         'idpDomain': 'perf244.com', 'totalUsers': 0},
        {'idpId': '9d3cf11a-bf96-4c1d-8367-7e5dad873b8a', 'idpDisplayName': 'ASTRA-OKTA-JIT6FWMIjit-idp',
         'idpDomain': 'perf173.com', 'totalUsers': 0},
        {'idpId': '3df76bab-a11b-4e21-b05c-fca2d60dd837', 'idpDisplayName': 'ASTRA-OKTA-JIT6LVVZjit-idp',
         'idpDomain': 'perf311.com', 'totalUsers': 0},
        {'idpId': '6287c4fa-b94e-4be6-a1e6-996a3ac44a89', 'idpDisplayName': 'ASTRA-OKTA-JIT8I7OKjit-idp',
         'idpDomain': 'perf273.com', 'totalUsers': 0},
        {'idpId': '1b3fa9e8-b0b8-4b13-9860-3cd602440eef', 'idpDisplayName': 'ASTRA-OKTA-JITVKI7Hjit-idp',
         'idpDomain': 'perf295.com', 'totalUsers': 0},
        {'idpId': '6f6b9c66-00ba-4d73-b078-9defff9fc72e', 'idpDisplayName': 'ASTRA-OKTA-JITHZI7Fjit-idp',
         'idpDomain': 'perf399.com', 'totalUsers': 0},
        {'idpId': 'a63b0ff8-bc09-4c9a-b50c-770d72de429d', 'idpDisplayName': 'ASTRA-OKTA-JITVWKJ7jit-idp',
         'idpDomain': 'perf485.com', 'totalUsers': 0},
        {'idpId': '40e05de5-21c7-472e-b9df-d1c04b2e01fd', 'idpDisplayName': 'ASTRA-OKTA-JITDL5KMjit-idp',
         'idpDomain': 'perf103.com', 'totalUsers': 0},
        {'idpId': '6a75a4d9-5583-41f2-84ee-874366a8675d', 'idpDisplayName': 'ASTRA-OKTA-JITJSYQLjit-idp',
         'idpDomain': 'perf85.com', 'totalUsers': 0},
        {'idpId': 'aec4927e-a953-4aea-9f58-54ef5d420a93', 'idpDisplayName': 'ASTRA-OKTA-JITBN1JSjit-idp',
         'idpDomain': 'perf230.com', 'totalUsers': 0},
        {'idpId': '08589aaf-c3be-49d2-95e0-88238b0ebb18', 'idpDisplayName': 'ASTRA-OKTA-JITWRLI9jit-idp',
         'idpDomain': 'perf196.com', 'totalUsers': 0},
        {'idpId': 'b8aba5ce-4386-4f53-946f-0feed87faa1a', 'idpDisplayName': 'ASTRA-OKTA-JITN2WC1jit-idp',
         'idpDomain': 'perf143.com', 'totalUsers': 0},
        {'idpId': '7bb3016b-0748-4b2d-b9a4-53b99c034b59', 'idpDisplayName': 'ASTRA-OKTA-JITB39KOjit-idp',
         'idpDomain': 'perf479.com', 'totalUsers': 0},
        {'idpId': '7ed1e2f9-146e-4e63-b121-9f8bf0d6e807', 'idpDisplayName': 'ASTRA-OKTA-JITVHQA8jit-idp',
         'idpDomain': 'perf125.com', 'totalUsers': 0},
        {'idpId': 'c3886b2a-df14-4c57-9388-5f6da09e37bc', 'idpDisplayName': 'ASTRA-OKTA-JITSV07Ejit-idp',
         'idpDomain': 'perf109.com', 'totalUsers': 0},
        {'idpId': 'aa073411-cfe3-47df-b0a1-acd5423fbab0', 'idpDisplayName': 'ASTRA-OKTA-JIT7I98Mjit-idp',
         'idpDomain': 'perf332.com', 'totalUsers': 0},
        {'idpId': 'b87963cc-1beb-4dfa-9e97-148928cbff05', 'idpDisplayName': 'ASTRA-OKTA-JITR60TDjit-idp',
         'idpDomain': 'perf340.com', 'totalUsers': 0},
        {'idpId': '1c683141-e30d-4c94-81b4-d25d09692ef4', 'idpDisplayName': 'ASTRA-OKTA-JITGB8FIjit-idp',
         'idpDomain': 'perf464.com', 'totalUsers': 0},
        {'idpId': '0cad1423-a024-4197-a1f7-cce8bf5c0b0d', 'idpDisplayName': 'ASTRA-OKTA-JITYSO6Ljit-idp',
         'idpDomain': 'perf127.com', 'totalUsers': 0},
        {'idpId': 'cb9f940f-8917-485e-9649-b3db49a24783', 'idpDisplayName': 'ASTRA-OKTA-JITNLN5Fjit-idp',
         'idpDomain': 'perf117.com', 'totalUsers': 0},
        {'idpId': '3e308e01-ebc0-40a5-86be-2db7e8d00307', 'idpDisplayName': 'ASTRA-OKTA-JIT5ATBXjit-idp',
         'idpDomain': 'perf349.com', 'totalUsers': 0},
        {'idpId': 'ffc9716b-802c-4601-80ee-bfbfac780b7b', 'idpDisplayName': 'ASTRA-OKTA-JITWF26Xjit-idp',
         'idpDomain': 'perf320.com', 'totalUsers': 0},
        {'idpId': '303f6e93-99e1-40a3-8cf4-abb6d9ba5213', 'idpDisplayName': 'ASTRA-OKTA-JITPQ4LTjit-idp',
         'idpDomain': 'perf49.com', 'totalUsers': 0},
        {'idpId': 'f375e5a8-590a-48cf-ad1c-ef5a5f16be80', 'idpDisplayName': 'ASTRA-OKTA-JIT84AKJjit-idp',
         'idpDomain': 'perf154.com', 'totalUsers': 0},
        {'idpId': '84e3d5d6-fb82-459d-b6d2-a5cac0d63623', 'idpDisplayName': 'ASTRA-OKTA-JITWZ7ORjit-idp',
         'idpDomain': 'perf304.com', 'totalUsers': 0},
        {'idpId': 'd76296eb-4ab1-4a70-a877-e063e97b80fe', 'idpDisplayName': 'ASTRA-OKTA-JITQ3287jit-idp',
         'idpDomain': 'perf43.com', 'totalUsers': 0},
        {'idpId': '6225175b-19bf-404e-a777-87f699b711ed', 'idpDisplayName': 'ASTRA-OKTA-JITQUWXTjit-idp',
         'idpDomain': 'perf148.com', 'totalUsers': 0},
        {'idpId': '23f2dd7e-8b48-41b0-8976-8cce08d8c78a', 'idpDisplayName': 'ASTRA-OKTA-JITUP0COjit-idp',
         'idpDomain': 'perf271.com', 'totalUsers': 0},
        {'idpId': '5847a667-9b7f-456d-bdc1-f6d45649e922', 'idpDisplayName': 'ASTRA-OKTA-JITPA7WHjit-idp',
         'idpDomain': 'perf453.com', 'totalUsers': 0},
        {'idpId': 'd910a25e-908a-4129-8ab2-8f53a527b45e', 'idpDisplayName': 'ASTRA-OKTA-JIT5I37Pjit-idp',
         'idpDomain': 'perf441.com', 'totalUsers': 0},
        {'idpId': 'e5cd2465-ade2-42d0-ab12-197e010b1286', 'idpDisplayName': 'ASTRA-OKTA-JITCGN2Jjit-idp',
         'idpDomain': 'perf205.com', 'totalUsers': 0},
        {'idpId': '9b0dfe0e-e1a9-4e10-b0e9-eb55f0be8e9b', 'idpDisplayName': 'ASTRA-OKTA-JITX1RDLjit-idp',
         'idpDomain': 'perf54.com', 'totalUsers': 0},
        {'idpId': 'ab3d20b0-af64-42ca-8fd9-cd2b1ddf71a3', 'idpDisplayName': 'ASTRA-OKTA-JITX80GGjit-idp',
         'idpDomain': 'perf27.com', 'totalUsers': 0},
        {'idpId': '1703e9a3-51b5-4afe-811e-fd99908bf0c0', 'idpDisplayName': 'ASTRA-OKTA-JITCPU5Tjit-idp',
         'idpDomain': 'perf108.com', 'totalUsers': 0},
        {'idpId': '673a3de6-126a-4df1-8331-a335e489fb3c', 'idpDisplayName': 'ASTRA-OKTA-JITNSM2Ejit-idp',
         'idpDomain': 'perf389.com', 'totalUsers': 0},
        {'idpId': '171d14e6-925d-489e-9427-543ba4fee2f8', 'idpDisplayName': 'ASTRA-OKTA-JITMZM7Hjit-idp',
         'idpDomain': 'perf111.com', 'totalUsers': 0},
        {'idpId': 'e35ae037-d31d-42dc-bd29-916bad189eba', 'idpDisplayName': 'ASTRA-OKTA-JIT40H5Cjit-idp',
         'idpDomain': 'perf10.com', 'totalUsers': 0},
        {'idpId': 'a0ddf3db-0fd1-4c14-9b4b-e4b84345a45b', 'idpDisplayName': 'ASTRA-OKTA-JIT106GPjit-idp',
         'idpDomain': 'perf146.com', 'totalUsers': 0},
        {'idpId': '74538636-87ce-47fa-94b5-669ae359de2a', 'idpDisplayName': 'ASTRA-OKTA-JIT3O6VHjit-idp',
         'idpDomain': 'perf87.com', 'totalUsers': 0},
        {'idpId': '5d95915b-df45-42a3-87f4-497030e47772', 'idpDisplayName': 'ASTRA-OKTA-JIT2G5QVjit-idp',
         'idpDomain': 'perf3.com', 'totalUsers': 0},
        {'idpId': '21ad3631-e13e-4679-a486-8e6a201b35d2', 'idpDisplayName': 'ASTRA-OKTA-JITV6F5Bjit-idp',
         'idpDomain': 'perf376.com', 'totalUsers': 0},
        {'idpId': '5306a10b-0069-4573-b3a3-85050c1881fd', 'idpDisplayName': 'ASTRA-OKTA-JITKRGT7jit-idp',
         'idpDomain': 'perf44.com', 'totalUsers': 0},
        {'idpId': '61a63601-b515-4325-916d-aa95660eff6d', 'idpDisplayName': 'ASTRA-OKTA-JIT7DEDCjit-idp',
         'idpDomain': 'perf379.com', 'totalUsers': 0},
        {'idpId': '802bac2e-ea18-4c35-9cb8-a95a043a6511', 'idpDisplayName': 'ASTRA-OKTA-JITML5KCjit-idp',
         'idpDomain': 'perf88.com', 'totalUsers': 0},
        {'idpId': '146a4b3d-dd04-49d1-99e2-454561ec10f2', 'idpDisplayName': 'ASTRA-OKTA-JITXFU7Zjit-idp',
         'idpDomain': 'perf190.com', 'totalUsers': 0},
        {'idpId': '0e56c935-16ca-4cef-b3c7-d9cc6c50df50', 'idpDisplayName': 'ASTRA-OKTA-JITNG97Hjit-idp',
         'idpDomain': 'perf370.com', 'totalUsers': 0},
        {'idpId': '076ee5b4-504a-461c-ae52-44b6f33e9aaa', 'idpDisplayName': 'ASTRA-OKTA-JITU6WK1jit-idp',
         'idpDomain': 'perf79.com', 'totalUsers': 0},
        {'idpId': '928bd2c0-50f5-4751-b298-a92d441b546f', 'idpDisplayName': 'ASTRA-OKTA-JITADOVFjit-idp',
         'idpDomain': 'perf415.com', 'totalUsers': 0},
        {'idpId': '61834c22-ffc3-43ca-9b0f-5f04895b61e3', 'idpDisplayName': 'ASTRA-OKTA-JITP4W1Gjit-idp',
         'idpDomain': 'perf156.com', 'totalUsers': 0},
        {'idpId': 'c19d16f3-7d9c-4908-a696-bf2d01a5255c', 'idpDisplayName': 'ASTRA-OKTA-JITT6IQUjit-idp',
         'idpDomain': 'perf274.com', 'totalUsers': 0},
        {'idpId': '73f34473-3352-4248-89f3-4b46bb756cff', 'idpDisplayName': 'ASTRA-OKTA-JIT6ES8Ijit-idp',
         'idpDomain': 'perf373.com', 'totalUsers': 0},
        {'idpId': '245e7b08-4dd2-4e3a-8dc6-122ff65457b6', 'idpDisplayName': 'ASTRA-OKTA-JITN7UOHjit-idp',
         'idpDomain': 'perf167.com', 'totalUsers': 0},
        {'idpId': '61a3ae34-a44c-49ce-a247-e6810b44e4a8', 'idpDisplayName': 'ASTRA-OKTA-JITNFW8Fjit-idp',
         'idpDomain': 'perf322.com', 'totalUsers': 0},
        {'idpId': '7759d412-964c-4781-b6f0-e2831e998d7e', 'idpDisplayName': 'ASTRA-OKTA-JITT5030jit-idp',
         'idpDomain': 'perf275.com', 'totalUsers': 0},
        {'idpId': '7cf770b2-a0e2-4050-b8cb-07da63ec68ae', 'idpDisplayName': 'ASTRA-OKTA-JITO34MTjit-idp',
         'idpDomain': 'perf366.com', 'totalUsers': 0},
        {'idpId': '6bc16403-34a9-4c27-bc35-8e6fd8ce5be6', 'idpDisplayName': 'ASTRA-OKTA-JIT0SQWLjit-idp',
         'idpDomain': 'perf157.com', 'totalUsers': 0},
        {'idpId': '2e3b7147-c484-49e9-a400-613ab1b7f247', 'idpDisplayName': 'ASTRA-OKTA-JITDYWXYjit-idp',
         'idpDomain': 'perf316.com', 'totalUsers': 0},
        {'idpId': 'bdab7a46-a262-48b6-80a3-956b7b69ba50', 'idpDisplayName': 'ASTRA-OKTA-JITTB5ZIjit-idp',
         'idpDomain': 'perf422.com', 'totalUsers': 0},
        {'idpId': '6dd1b648-2885-44fc-a8a3-e6a39fc0ade9', 'idpDisplayName': 'ASTRA-OKTA-JITSFJRJjit-idp',
         'idpDomain': 'perf137.com', 'totalUsers': 0},
        {'idpId': '5dcdd8ee-53b1-4663-a850-ecd1adc2080a', 'idpDisplayName': 'ASTRA-OKTA-JITKS3BKjit-idp',
         'idpDomain': 'perf123.com', 'totalUsers': 0},
        {'idpId': '98010efa-032d-4f5a-a965-8df20a0fc682', 'idpDisplayName': 'ASTRA-OKTA-JITXLFWUjit-idp',
         'idpDomain': 'perf121.com', 'totalUsers': 0},
        {'idpId': '2400d401-ff11-4dc7-a535-e75ed77065aa', 'idpDisplayName': 'ASTRA-OKTA-JITR1WUAjit-idp',
         'idpDomain': 'perf263.com', 'totalUsers': 0},
        {'idpId': 'aa497ca8-6f68-4111-a116-2fde6ff974e6', 'idpDisplayName': 'ASTRA-OKTA-JITSOT58jit-idp',
         'idpDomain': 'perf401.com', 'totalUsers': 0},
        {'idpId': '343df1e1-3ffd-43ea-a65c-1afeea9c328e', 'idpDisplayName': 'ASTRA-OKTA-JITTMC5Xjit-idp',
         'idpDomain': 'perf430.com', 'totalUsers': 0},
        {'idpId': 'e27a89c9-1a3f-493f-aac4-fd8472462d0b', 'idpDisplayName': 'ASTRA-OKTA-JITNNIIIjit-idp',
         'idpDomain': 'perf118.com', 'totalUsers': 0},
        {'idpId': '76f9f589-18ed-42f3-a593-194c93c8ed1f', 'idpDisplayName': 'ASTRA-OKTA-JITXY24Hjit-idp',
         'idpDomain': 'perf207.com', 'totalUsers': 0},
        {'idpId': '3f161202-b511-4215-9a8d-84679713a327', 'idpDisplayName': 'ASTRA-OKTA-JITJ45LLjit-idp',
         'idpDomain': 'perf299.com', 'totalUsers': 0},
        {'idpId': 'ae8a1cb9-f690-4c29-a80d-c30b1ebd2efc', 'idpDisplayName': 'ASTRA-OKTA-JITB5WASjit-idp',
         'idpDomain': 'perf348.com', 'totalUsers': 0},
        {'idpId': 'b92833a1-2dff-4b35-88e3-3ea29d262553', 'idpDisplayName': 'ASTRA-OKTA-JITAOS1Xjit-idp',
         'idpDomain': 'perf6.com', 'totalUsers': 0},
        {'idpId': 'b2b5d7e4-24b2-4ae5-b999-53479acd796f', 'idpDisplayName': 'ASTRA-OKTA-JITKAW5Kjit-idp',
         'idpDomain': 'perf357.com', 'totalUsers': 0},
        {'idpId': '7a065b57-4d47-4722-aec5-2e41061b5e17', 'idpDisplayName': 'ASTRA-OKTA-JITT0KJ5jit-idp',
         'idpDomain': 'perf214.com', 'totalUsers': 0},
        {'idpId': '041bc1a6-a302-4d64-ad63-e423290acfe9', 'idpDisplayName': 'ASTRA-OKTA-JIT0WHYAjit-idp',
         'idpDomain': 'perf97.com', 'totalUsers': 0},
        {'idpId': 'af0dd54a-06af-41ec-bd87-0ec589068f37', 'idpDisplayName': 'ASTRA-OKTA-JITFHKDBjit-idp',
         'idpDomain': 'perf288.com', 'totalUsers': 0},
        {'idpId': '63945d9b-84e0-47f9-9a37-94b5b4800655', 'idpDisplayName': 'ASTRA-OKTA-JIT4I76Pjit-idp',
         'idpDomain': 'perf321.com', 'totalUsers': 0},
        {'idpId': '98b6f849-1fe1-499c-bc92-dea8efebc594', 'idpDisplayName': 'ASTRA-OKTA-JITH3LBXjit-idp',
         'idpDomain': 'perf364.com', 'totalUsers': 0},
        {'idpId': '1f61f98e-1c88-4127-8b8d-386e26a0b71d', 'idpDisplayName': 'ASTRA-OKTA-JITWMVDDjit-idp',
         'idpDomain': 'perf264.com', 'totalUsers': 0},
        {'idpId': 'bc099118-6aeb-4df7-9bb6-b03eec734132', 'idpDisplayName': 'ASTRA-OKTA-JITO10JMjit-idp',
         'idpDomain': 'perf142.com', 'totalUsers': 0},
        {'idpId': '53448972-ccd8-4162-b1dd-804a752b8384', 'idpDisplayName': 'ASTRA-OKTA-JIT3HAA4jit-idp',
         'idpDomain': 'perf451.com', 'totalUsers': 0},
        {'idpId': '5b2891e9-f79c-4aa0-8799-024b2ac2dc10', 'idpDisplayName': 'ASTRA-OKTA-JITDTCI1jit-idp',
         'idpDomain': 'perf296.com', 'totalUsers': 0},
        {'idpId': '74c8499e-98bd-4bf7-9d44-eb56c836ac68', 'idpDisplayName': 'ASTRA-OKTA-JIT80ZNKjit-idp',
         'idpDomain': 'perf338.com', 'totalUsers': 0},
        {'idpId': 'bab679fe-011f-479a-9300-337f078aad99', 'idpDisplayName': 'ASTRA-OKTA-JIT7MHHPjit-idp',
         'idpDomain': 'perf302.com', 'totalUsers': 0},
        {'idpId': '48f9486a-fce8-4d35-92ae-a23dfe301683', 'idpDisplayName': 'ASTRA-OKTA-JITCD98Jjit-idp',
         'idpDomain': 'perf470.com', 'totalUsers': 0},
        {'idpId': 'e785687c-28c1-42a4-9805-ef8d860a43ce', 'idpDisplayName': 'ASTRA-OKTA-JITTBI6Jjit-idp',
         'idpDomain': 'perf354.com', 'totalUsers': 0},
        {'idpId': '6d20fd50-5ee7-40ff-97cd-c9be9b217a51', 'idpDisplayName': 'ASTRA-OKTA-JITFTZB8jit-idp',
         'idpDomain': 'perf193.com', 'totalUsers': 0},
        {'idpId': '5c3a4367-ebd6-4839-887e-36524daaf5b3', 'idpDisplayName': 'ASTRA-OKTA-JITXOGCWjit-idp',
         'idpDomain': 'perf29.com', 'totalUsers': 0},
        {'idpId': 'b67edc54-b165-4d7d-b255-473275bb47b3', 'idpDisplayName': 'ASTRA-OKTA-JITGYP0Bjit-idp',
         'idpDomain': 'perf22.com', 'totalUsers': 0},
        {'idpId': 'f989d807-f471-4418-ac25-171d339de221', 'idpDisplayName': 'ASTRA-OKTA-JITB0OC9jit-idp',
         'idpDomain': 'perf432.com', 'totalUsers': 0},
        {'idpId': 'f4ce7c1a-6085-49fc-84db-b5c8e585ce37', 'idpDisplayName': 'ASTRA-OKTA-JITAS3FSjit-idp',
         'idpDomain': 'perf81.com', 'totalUsers': 0},
        {'idpId': 'bd0c565e-7af0-466b-9811-e4968fa5d6ad', 'idpDisplayName': 'ASTRA-OKTA-JIT8DFJ0jit-idp',
         'idpDomain': 'perf151.com', 'totalUsers': 0},
        {'idpId': '4c6a56f4-a3fc-48ff-a90c-0c1fcd4bf164', 'idpDisplayName': 'ASTRA-OKTA-JIT0JICDjit-idp',
         'idpDomain': 'perf213.com', 'totalUsers': 0},
        {'idpId': '8fa34cfd-233d-480f-9f8b-58b30f9fae52', 'idpDisplayName': 'ASTRA-OKTA-JITA2Y0Ljit-idp',
         'idpDomain': 'perf33.com', 'totalUsers': 0},
        {'idpId': '58dbf610-858b-4249-a0ef-143e4a2dd68f', 'idpDisplayName': 'ASTRA-OKTA-JITVLEOCjit-idp',
         'idpDomain': 'perf57.com', 'totalUsers': 0},
        {'idpId': '8a121e78-fa1d-4f2f-ae85-c621bce9a1d9', 'idpDisplayName': 'ASTRA-OKTA-JITLMAOXjit-idp',
         'idpDomain': 'perf359.com', 'totalUsers': 0},
        {'idpId': '88ced75c-5322-4776-bab0-3d023a2d5535', 'idpDisplayName': 'ASTRA-OKTA-JIT4NSDRjit-idp',
         'idpDomain': 'perf336.com', 'totalUsers': 0},
        {'idpId': '2764e4da-0eec-46ae-ab12-45b0022007c7', 'idpDisplayName': 'ASTRA-OKTA-JITOXX8Ajit-idp',
         'idpDomain': 'perf203.com', 'totalUsers': 0},
        {'idpId': '1ca9b0b8-0e86-4953-88b9-06d858ce5443', 'idpDisplayName': 'ASTRA-OKTA-JITY8ORXjit-idp',
         'idpDomain': 'perf416.com', 'totalUsers': 0},
        {'idpId': '43514ae0-9b10-43d1-877d-9296aece11bb', 'idpDisplayName': 'ASTRA-OKTA-JITAZ08Kjit-idp',
         'idpDomain': 'perf24.com', 'totalUsers': 0},
        {'idpId': 'eeb9a2a4-15a0-4ca5-8557-56918b948dd8', 'idpDisplayName': 'ASTRA-OKTA-JIT6WOPYjit-idp',
         'idpDomain': 'perf70.com', 'totalUsers': 0},
        {'idpId': 'f4b7dd4a-9d0d-4f41-a021-d8ca19eb6c3f', 'idpDisplayName': 'ASTRA-OKTA-JIT09N1Rjit-idp',
         'idpDomain': 'perf140.com', 'totalUsers': 0},
        {'idpId': '971587e1-78b4-4e9c-9dfa-2d7c5f583dcb', 'idpDisplayName': 'ASTRA-OKTA-JIT53OIEjit-idp',
         'idpDomain': 'perf420.com', 'totalUsers': 0},
        {'idpId': 'de77743a-4454-452c-a040-221821dc11c8', 'idpDisplayName': 'ASTRA-OKTA-JITL3XSMjit-idp',
         'idpDomain': 'perf128.com', 'totalUsers': 0},
        {'idpId': 'ef745b67-e2ff-44b1-828c-452e66b7b460', 'idpDisplayName': 'ASTRA-OKTA-JITKN850jit-idp',
         'idpDomain': 'perf491.com', 'totalUsers': 0},
        {'idpId': '25577920-2c2b-41a8-83c9-4925ca53997e', 'idpDisplayName': 'ASTRA-OKTA-JITA4YEIjit-idp',
         'idpDomain': 'perf216.com', 'totalUsers': 0},
        {'idpId': '21af1d94-e894-4f7a-8b51-fe1c35cf7d61', 'idpDisplayName': 'ASTRA-OKTA-JIT5O1FIjit-idp',
         'idpDomain': 'perf133.com', 'totalUsers': 0},
        {'idpId': '89aa28f8-01f5-4cd5-ae0d-107f90eb0aa8', 'idpDisplayName': 'ASTRA-OKTA-JITRWMVXjit-idp',
         'idpDomain': 'perf333.com', 'totalUsers': 0},
        {'idpId': '696dd019-430d-422f-8c0b-2644d503b669', 'idpDisplayName': 'ASTRA-OKTA-JITQ7VYMjit-idp',
         'idpDomain': 'perf107.com', 'totalUsers': 0},
        {'idpId': '9ce2cc37-fa0f-4e07-bd47-a9bbc4b13735', 'idpDisplayName': 'ASTRA-OKTA-JIT7N8QPjit-idp',
         'idpDomain': 'perf447.com', 'totalUsers': 0},
        {'idpId': '6d3f4c44-c82e-48c7-a25b-24a871ecba0c', 'idpDisplayName': 'ASTRA-OKTA-JITX1SOEjit-idp',
         'idpDomain': 'perf428.com', 'totalUsers': 0},
        {'idpId': '51f80d5e-1412-405c-bbbe-3d2b6d7728eb', 'idpDisplayName': 'ASTRA-OKTA-JITI3PR0jit-idp',
         'idpDomain': 'perf290.com', 'totalUsers': 0},
        {'idpId': '7af19df0-f764-4354-8d3f-667fb504182d', 'idpDisplayName': 'ASTRA-OKTA-JITPAUOVjit-idp',
         'idpDomain': 'perf360.com', 'totalUsers': 0},
        {'idpId': 'ab3edf9b-5f8f-430f-bc6e-1fc290c992de', 'idpDisplayName': 'ASTRA-OKTA-JIT1G396jit-idp',
         'idpDomain': 'perf476.com', 'totalUsers': 0},
        {'idpId': '7ec46e19-00bc-4538-92df-f85649b4234c', 'idpDisplayName': 'ASTRA-OKTA-JIT7SFTOjit-idp',
         'idpDomain': 'perf259.com', 'totalUsers': 0},
        {'idpId': '5f544d11-b197-4987-9841-2cd613d3ebea', 'idpDisplayName': 'ASTRA-OKTA-JITY00UBjit-idp',
         'idpDomain': 'perf35.com', 'totalUsers': 0},
        {'idpId': '9cf5185c-f62b-468e-b28e-e7297d98661f', 'idpDisplayName': 'ASTRA-OKTA-JITTEW5Kjit-idp',
         'idpDomain': 'perf371.com', 'totalUsers': 0},
        {'idpId': '0a509fc8-439a-4371-a8dd-7437137cad6b', 'idpDisplayName': 'ASTRA-OKTA-JIT7OGFOjit-idp',
         'idpDomain': 'perf212.com', 'totalUsers': 0},
        {'idpId': 'b991ab07-059b-4573-b7bf-1f12a19e921f', 'idpDisplayName': 'ASTRA-OKTA-JITB8XN3jit-idp',
         'idpDomain': 'perf197.com', 'totalUsers': 0},
        {'idpId': '1b34ef0e-4aad-480a-afd0-ab5089884e09', 'idpDisplayName': 'ASTRA-OKTA-JIT4LFJGjit-idp',
         'idpDomain': 'perf164.com', 'totalUsers': 0},
        {'idpId': '83d7c0ba-0108-4e00-8f3c-c0f7c0c7dae3', 'idpDisplayName': 'ASTRA-OKTA-JITHK905jit-idp',
         'idpDomain': 'perf86.com', 'totalUsers': 0},
        {'idpId': '133975f9-d101-458d-8378-7fe00275ac60', 'idpDisplayName': 'ASTRA-OKTA-JITLQQS8jit-idp',
         'idpDomain': 'perf94.com', 'totalUsers': 0},
        {'idpId': 'ade8de19-4789-4f65-9699-d6d4eae26467', 'idpDisplayName': 'ASTRA-OKTA-JITAT78Gjit-idp',
         'idpDomain': 'perf425.com', 'totalUsers': 0},
        {'idpId': '391d6e5b-405a-4a19-9b60-1d473c5a74d1', 'idpDisplayName': 'ASTRA-OKTA-JITIMGQLjit-idp',
         'idpDomain': 'perf381.com', 'totalUsers': 0},
        {'idpId': '032cf5c8-3f7f-4714-8933-e3e6ff73f7b9', 'idpDisplayName': 'ASTRA-OKTA-JITUMSFBjit-idp',
         'idpDomain': 'perf184.com', 'totalUsers': 0},
        {'idpId': '4db05556-8012-4755-abb4-1a954d190de5', 'idpDisplayName': 'ASTRA-OKTA-JITWKOV0jit-idp',
         'idpDomain': 'perf219.com', 'totalUsers': 0},
        {'idpId': 'c0797866-106b-41b9-b511-ebc2f5f0e332', 'idpDisplayName': 'ASTRA-OKTA-JIT57TP2jit-idp',
         'idpDomain': 'perf443.com', 'totalUsers': 0},
        {'idpId': 'ce28b472-4e47-455f-9e7e-4bcc8881a67b', 'idpDisplayName': 'ASTRA-OKTA-JITCTQ2Gjit-idp',
         'idpDomain': 'perf19.com', 'totalUsers': 0},
        {'idpId': 'ee5493b8-4a8f-48bb-ab05-737b2a5325ac', 'idpDisplayName': 'ASTRA-OKTA-JITUYKSMjit-idp',
         'idpDomain': 'perf393.com', 'totalUsers': 0},
        {'idpId': 'cf70e57e-2b12-496f-b8f7-e65ce0117d29', 'idpDisplayName': 'ASTRA-OKTA-JITAVNN5jit-idp',
         'idpDomain': 'perf75.com', 'totalUsers': 0},
        {'idpId': '8ffca798-c756-4c25-b068-fc38daf7f1e0', 'idpDisplayName': 'ASTRA-OKTA-JIT5MIMSjit-idp',
         'idpDomain': 'perf450.com', 'totalUsers': 0},
        {'idpId': 'afdc0fb7-145f-4dfb-b615-5fe4497f175e', 'idpDisplayName': 'ASTRA-OKTA-JITVZBPRjit-idp',
         'idpDomain': 'perf136.com', 'totalUsers': 0},
        {'idpId': 'a1c07ddf-59f6-4c6e-8a41-5e50d79883a0', 'idpDisplayName': 'ASTRA-OKTA-JITOTGRXjit-idp',
         'idpDomain': 'perf254.com', 'totalUsers': 0},
        {'idpId': 'a4768457-07f6-4282-b870-78dc4f65bbb9', 'idpDisplayName': 'ASTRA-OKTA-JITFEPKIjit-idp',
         'idpDomain': 'perf253.com', 'totalUsers': 0},
        {'idpId': '98c7aeb8-be8a-49d7-9f54-53e1b38158f5', 'idpDisplayName': 'ASTRA-OKTA-JIT6FF29jit-idp',
         'idpDomain': 'perf250.com', 'totalUsers': 0},
        {'idpId': '1a1c0bd1-e53e-486a-84bd-36d8abcf476f', 'idpDisplayName': 'ASTRA-OKTA-JITCNHXVjit-idp',
         'idpDomain': 'perf25.com', 'totalUsers': 0},
        {'idpId': '9c8df79f-0362-4ada-b343-896f312a9a0c', 'idpDisplayName': 'ASTRA-OKTA-JITVF1F2jit-idp',
         'idpDomain': 'perf36.com', 'totalUsers': 0},
        {'idpId': 'f9d73a4c-4a1a-4282-97f0-976f9a2d8ce8', 'idpDisplayName': 'ASTRA-OKTA-JITQ1DCDjit-idp',
         'idpDomain': 'perf221.com', 'totalUsers': 0},
        {'idpId': 'c88d1f6d-fb8b-4b61-9871-b9c3a675695c', 'idpDisplayName': 'ASTRA-OKTA-JITVRKKMjit-idp',
         'idpDomain': 'perf472.com', 'totalUsers': 0},
        {'idpId': '8fea52f9-ee9f-4d79-a9c2-12c4966d8fea', 'idpDisplayName': 'ASTRA-OKTA-JIT73AHWjit-idp',
         'idpDomain': 'perf238.com', 'totalUsers': 0},
        {'idpId': '53eb25d9-5b2b-4659-868c-1f0fdf80d519', 'idpDisplayName': 'ASTRA-OKTA-JIT8Q6RCjit-idp',
         'idpDomain': 'perf172.com', 'totalUsers': 0},
        {'idpId': '711126f6-bc0d-41b2-83b5-8b36645232eb', 'idpDisplayName': 'ASTRA-OKTA-JITRCWKAjit-idp',
         'idpDomain': 'perf51.com', 'totalUsers': 0},
        {'idpId': 'e77b1ab0-83d9-4ede-8db9-2513bf3d993e', 'idpDisplayName': 'ASTRA-OKTA-JITJIIU5jit-idp',
         'idpDomain': 'perf240.com', 'totalUsers': 0},
        {'idpId': '70191cb4-f7c8-46cf-a2d8-9c547dd818c6', 'idpDisplayName': 'ASTRA-OKTA-JIT4JQGMjit-idp',
         'idpDomain': 'perf459.com', 'totalUsers': 0},
        {'idpId': '3236e1ea-9feb-4dd4-8109-975affdbe953', 'idpDisplayName': 'ASTRA-OKTA-JIT3Y2FNjit-idp',
         'idpDomain': 'perf101.com', 'totalUsers': 0},
        {'idpId': '8cb11591-673f-48a0-a19f-07834cff3602', 'idpDisplayName': 'ASTRA-OKTA-JITI705Hjit-idp',
         'idpDomain': 'perf445.com', 'totalUsers': 0},
        {'idpId': '5f549079-53ca-4d90-a5dc-8cb026dd6bd5', 'idpDisplayName': 'ASTRA-OKTA-JITVLXI8jit-idp',
         'idpDomain': 'perf171.com', 'totalUsers': 0},
        {'idpId': '8f3144db-19bf-4387-9e5d-62caaf8b785d', 'idpDisplayName': 'ASTRA-OKTA-JIT3V4EOjit-idp',
         'idpDomain': 'perf237.com', 'totalUsers': 0},
        {'idpId': 'dabbd2a4-1e97-4dbb-8187-804ae59fab2f', 'idpDisplayName': 'ASTRA-OKTA-JITUNJZLjit-idp',
         'idpDomain': 'perf241.com', 'totalUsers': 0},
        {'idpId': 'cf5f94e9-9ad3-48a1-8d05-c067da6c05fd', 'idpDisplayName': 'ASTRA-OKTA-JITG9EKIjit-idp',
         'idpDomain': 'perf439.com', 'totalUsers': 0},
        {'idpId': 'f2dc6237-cb38-4a34-9b11-79dd713b6e45', 'idpDisplayName': 'ASTRA-OKTA-JITFVBJ6jit-idp',
         'idpDomain': 'perf466.com', 'totalUsers': 0},
        {'idpId': '8434645b-a282-4ee6-9c3c-d65ea00894c2', 'idpDisplayName': 'ASTRA-OKTA-JIT4Y1FXjit-idp',
         'idpDomain': 'perf236.com', 'totalUsers': 0},
        {'idpId': '7c01b01c-a517-41cc-8c48-c8d3791237fb', 'idpDisplayName': 'ASTRA-OKTA-JITMC536jit-idp',
         'idpDomain': 'perf261.com', 'totalUsers': 0},
        {'idpId': '20ad0a47-1910-4ad2-94f9-cd9761b8fb23', 'idpDisplayName': 'ASTRA-OKTA-JITX0VVNjit-idp',
         'idpDomain': 'perf120.com', 'totalUsers': 0},
        {'idpId': '15ff9a25-afce-42ce-9982-503442d706f1', 'idpDisplayName': 'ASTRA-OKTA-JITWRCTIjit-idp',
         'idpDomain': 'perf395.com', 'totalUsers': 0},
        {'idpId': 'eaf277c9-2b06-413a-ad08-66f8c122a0c0', 'idpDisplayName': 'ASTRA-OKTA-JITLYAXUjit-idp',
         'idpDomain': 'perf234.com', 'totalUsers': 0},
        {'idpId': 'f1ee8d26-3d94-465d-809a-4337459a72a3', 'idpDisplayName': 'ASTRA-OKTA-JITVTKHQjit-idp',
         'idpDomain': 'perf256.com', 'totalUsers': 0},
        {'idpId': '635c25b6-00d5-4f61-8948-ea726b419b39', 'idpDisplayName': 'ASTRA-OKTA-JIT0Z9GOjit-idp',
         'idpDomain': 'perf392.com', 'totalUsers': 0},
        {'idpId': 'e885897e-b3c8-4d3e-8b98-efc0c9309a8f', 'idpDisplayName': 'ASTRA-OKTA-JIT9MECRjit-idp',
         'idpDomain': 'perf194.com', 'totalUsers': 0},
        {'idpId': 'ebc3857e-e6be-4589-a118-6888741ac62a', 'idpDisplayName': 'ASTRA-OKTA-JITKTG2Yjit-idp',
         'idpDomain': 'perf228.com', 'totalUsers': 0},
        {'idpId': '31f199af-fad9-4581-98a8-14f1fab3efe4', 'idpDisplayName': 'ASTRA-OKTA-JITB5SCXjit-idp',
         'idpDomain': 'perf185.com', 'totalUsers': 0},
        {'idpId': 'bc63024c-5904-43b4-bf6a-f9973b2becfb', 'idpDisplayName': 'ASTRA-OKTA-JITALAOGjit-idp',
         'idpDomain': 'perf34.com', 'totalUsers': 0},
        {'idpId': 'fd4658d9-6383-4a5b-a292-43d6c5027526', 'idpDisplayName': 'ASTRA-OKTA-JITT3LBXjit-idp',
         'idpDomain': 'perf47.com', 'totalUsers': 0},
        {'idpId': '406ce61c-bf3f-4e20-8083-f96c070bb0d0', 'idpDisplayName': 'ASTRA-OKTA-JITTDS7Ojit-idp',
         'idpDomain': 'perf116.com', 'totalUsers': 0},
        {'idpId': '527d9545-0ff4-4168-b274-cdf34008d433', 'idpDisplayName': 'ASTRA-OKTA-JIT2R4GLjit-idp',
         'idpDomain': 'perf342.com', 'totalUsers': 0},
        {'idpId': 'b8d50bf4-dfba-48c9-ba89-c8a80f1f834c', 'idpDisplayName': 'ASTRA-OKTA-JITF8CA3jit-idp',
         'idpDomain': 'perf209.com', 'totalUsers': 0},
        {'idpId': '67a8cfc0-04a3-40ff-acc2-c66fedbb007d', 'idpDisplayName': 'ASTRA-OKTA-JITZG9TTjit-idp',
         'idpDomain': 'perf61.com', 'totalUsers': 0},
        {'idpId': '557b4c41-8e1f-4996-b9dd-4cddda90d536', 'idpDisplayName': 'ASTRA-OKTA-JITHR2RRjit-idp',
         'idpDomain': 'perf72.com', 'totalUsers': 0},
        {'idpId': '31d42967-c884-436b-8139-ee003f634010', 'idpDisplayName': 'ASTRA-OKTA-JIT8PIMMjit-idp',
         'idpDomain': 'perf95.com', 'totalUsers': 0},
        {'idpId': '30733c05-99d5-412b-8e96-b084c40ab380', 'idpDisplayName': 'ASTRA-OKTA-JITHSULKjit-idp',
         'idpDomain': 'perf369.com', 'totalUsers': 0},
        {'idpId': '84684fb5-f561-4c2b-b074-485582628277', 'idpDisplayName': 'ASTRA-OKTA-JITRMX34jit-idp',
         'idpDomain': 'perf179.com', 'totalUsers': 0},
        {'idpId': '3bda48b0-4529-46f0-8cf0-fd3082dbf89c', 'idpDisplayName': 'ASTRA-OKTA-JITVCBVKjit-idp',
         'idpDomain': 'perf178.com', 'totalUsers': 0},
        {'idpId': 'b5a1bea5-8ffd-4dff-bad1-52d9f71992a6', 'idpDisplayName': 'ASTRA-OKTA-JITUIDA0jit-idp',
         'idpDomain': 'perf305.com', 'totalUsers': 0},
        {'idpId': 'a307348a-9890-4e40-b581-c688bdf5e676', 'idpDisplayName': 'ASTRA-OKTA-JITG7SKBjit-idp',
         'idpDomain': 'perf298.com', 'totalUsers': 0},
        {'idpId': '35a53696-17c4-4ea6-9815-6355473826b7', 'idpDisplayName': 'ASTRA-OKTA-JITGJTJGjit-idp',
         'idpDomain': 'perf457.com', 'totalUsers': 0},
        {'idpId': 'd9508333-8b98-4b28-bd82-6a5178f3a421', 'idpDisplayName': 'ASTRA-OKTA-JITO68HGjit-idp',
         'idpDomain': 'perf303.com', 'totalUsers': 0},
        {'idpId': 'd2c28c1f-0862-4e54-bbb8-7bd82917a18e', 'idpDisplayName': 'ASTRA-OKTA-JIT4XPTDjit-idp',
         'idpDomain': 'perf183.com', 'totalUsers': 0},
        {'idpId': '5dadbd26-734d-4bba-a76e-2df26c27faff', 'idpDisplayName': 'ASTRA-OKTA-JIT8VFC8jit-idp',
         'idpDomain': 'perf417.com', 'totalUsers': 0},
        {'idpId': '789a1dad-6b93-45aa-9801-0aa5e48881f4', 'idpDisplayName': 'ASTRA-OKTA-JIT1SXUNjit-idp',
         'idpDomain': 'perf220.com', 'totalUsers': 0},
        {'idpId': '92114884-1828-4b90-8a16-38d0e0a1d2bd', 'idpDisplayName': 'ASTRA-OKTA-JIT1BPBQjit-idp',
         'idpDomain': 'perf358.com', 'totalUsers': 0},
        {'idpId': '32ac3d55-4b82-49c2-a136-91a87f1b8ad8', 'idpDisplayName': 'ASTRA-OKTA-JITLRTEMjit-idp',
         'idpDomain': 'perf480.com', 'totalUsers': 0},
        {'idpId': '96e34ed7-a520-40f5-9e56-29aece4b90b5', 'idpDisplayName': 'ASTRA-OKTA-JIT1RL9Vjit-idp',
         'idpDomain': 'perf268.com', 'totalUsers': 0},
        {'idpId': 'abfe584e-fee7-4f59-b06b-006ea4cabc6d', 'idpDisplayName': 'ASTRA-OKTA-JITUZZIJjit-idp',
         'idpDomain': 'perf313.com', 'totalUsers': 0},
        {'idpId': '072c9bf6-c70e-4ba3-8488-007e286f69ac', 'idpDisplayName': 'ASTRA-OKTA-JITLRQAYjit-idp',
         'idpDomain': 'perf284.com', 'totalUsers': 0},
        {'idpId': 'd41a54f6-e392-4733-ac71-0388e6170a2c', 'idpDisplayName': 'ASTRA-OKTA-JITUWRUEjit-idp',
         'idpDomain': 'perf9.com', 'totalUsers': 0},
        {'idpId': 'a99cea02-bbcf-46ce-b1d6-bca118130918', 'idpDisplayName': 'ASTRA-OKTA-JITYNG8Jjit-idp',
         'idpDomain': 'perf84.com', 'totalUsers': 0},
        {'idpId': '3e674911-b9c7-4db1-b462-10d63015f894', 'idpDisplayName': 'ASTRA-OKTA-JITVWOCMjit-idp',
         'idpDomain': 'perf407.com', 'totalUsers': 0},
        {'idpId': '414b0117-b025-4a48-944f-d53ab68c4e9f', 'idpDisplayName': 'ASTRA-OKTA-JITXEDHBjit-idp',
         'idpDomain': 'perf135.com', 'totalUsers': 0},
        {'idpId': 'd04aafdf-5291-478c-a4b5-46938527c92c', 'idpDisplayName': 'ASTRA-OKTA-JITMAPRTjit-idp',
         'idpDomain': 'perf327.com', 'totalUsers': 0},
        {'idpId': '628394aa-6651-4281-9b26-9d9e73dbe0a2', 'idpDisplayName': 'ASTRA-OKTA-JIT81SD6jit-idp',
         'idpDomain': 'perf481.com', 'totalUsers': 0},
        {'idpId': '902f2980-123a-4bfe-a7c3-0048028abec2', 'idpDisplayName': 'ASTRA-OKTA-JITT5AD5jit-idp',
         'idpDomain': 'perf215.com', 'totalUsers': 0},
        {'idpId': 'e27c126d-d22a-435d-950d-678d8bb9d9e6', 'idpDisplayName': 'ASTRA-OKTA-JITY1M1Ojit-idp',
         'idpDomain': 'perf413.com', 'totalUsers': 0},
        {'idpId': '45d253d5-fdcf-4587-ba2b-7da7068771e9', 'idpDisplayName': 'ASTRA-OKTA-JIT6TVY8jit-idp',
         'idpDomain': 'perf326.com', 'totalUsers': 0},
        {'idpId': 'dfef8c65-8d85-4e43-a643-b2169c4cb841', 'idpDisplayName': 'ASTRA-OKTA-JITZ10SMjit-idp',
         'idpDomain': 'perf245.com', 'totalUsers': 0},
        {'idpId': '463e07ba-8f3f-4ed2-8dda-5f05d6fe08bd', 'idpDisplayName': 'ASTRA-OKTA-JITDZ424jit-idp',
         'idpDomain': 'perf431.com', 'totalUsers': 0},
        {'idpId': '87cb6d42-e5c9-418a-8aa7-c95b407dd18e', 'idpDisplayName': 'ASTRA-OKTA-JITXS2DKjit-idp',
         'idpDomain': 'perf382.com', 'totalUsers': 0},
        {'idpId': '613a5ed9-37a7-492d-8075-02f895759e35', 'idpDisplayName': 'ASTRA-OKTA-JITHDF8Wjit-idp',
         'idpDomain': 'perf292.com', 'totalUsers': 0},
        {'idpId': '1dc92635-2c21-401e-81e6-98fcbab4007f', 'idpDisplayName': 'ASTRA-OKTA-JITZSQLJjit-idp',
         'idpDomain': 'perf347.com', 'totalUsers': 0},
        {'idpId': '5c971a2b-3fd3-40dd-8ff9-43255775b7fa', 'idpDisplayName': 'ASTRA-OKTA-JITM6YIZjit-idp',
         'idpDomain': 'perf187.com', 'totalUsers': 0},
        {'idpId': '2c4b29fc-4175-45f3-b7a5-9b8187e9d0de', 'idpDisplayName': 'ASTRA-OKTA-JITIFJH3jit-idp',
         'idpDomain': 'perf180.com', 'totalUsers': 0},
        {'idpId': '81250452-cc42-4434-badc-4805a5d0b7aa', 'idpDisplayName': 'ASTRA-OKTA-JITK51HWjit-idp',
         'idpDomain': 'perf177.com', 'totalUsers': 0},
        {'idpId': 'c10f002f-5181-437c-86dd-4ca242ce082f', 'idpDisplayName': 'ASTRA-OKTA-JITGC0AKjit-idp',
         'idpDomain': 'perf478.com', 'totalUsers': 0},
        {'idpId': 'bf5caedd-f13a-4cb6-9c64-b1fb672557b1', 'idpDisplayName': 'ASTRA-OKTA-JIT94A56jit-idp',
         'idpDomain': 'perf257.com', 'totalUsers': 0},
        {'idpId': '35cb60eb-f871-4d92-a5d0-1cabe1d8a60e', 'idpDisplayName': 'ASTRA-OKTA-JITT31WLjit-idp',
         'idpDomain': 'perf477.com', 'totalUsers': 0},
        {'idpId': '772dc804-af75-4cbc-a623-f6f894e29de2', 'idpDisplayName': 'ASTRA-OKTA-JIT059APjit-idp',
         'idpDomain': 'perf460.com', 'totalUsers': 0},
        {'idpId': 'acea1260-170a-4208-be27-0992b04198a4', 'idpDisplayName': 'ASTRA-OKTA-JITSR5OQjit-idp',
         'idpDomain': 'perf191.com', 'totalUsers': 0},
        {'idpId': '443b5775-01f0-46b6-8f9f-28befe81c4a1', 'idpDisplayName': 'ASTRA-OKTA-JIT5ZJIRjit-idp',
         'idpDomain': 'perf435.com', 'totalUsers': 0},
        {'idpId': '7345e288-ee3a-49b9-b3c9-ea65f1f89108', 'idpDisplayName': 'ASTRA-OKTA-JITH9CY6jit-idp',
         'idpDomain': 'perf469.com', 'totalUsers': 0},
        {'idpId': 'c7de55e3-89bb-4b9e-862b-57d92d47236e', 'idpDisplayName': 'ASTRA-OKTA-JIT3ZJHEjit-idp',
         'idpDomain': 'perf462.com', 'totalUsers': 0},
        {'idpId': '521d09ac-e1c3-4fd5-867e-a717617067f1', 'idpDisplayName': 'ASTRA-OKTA-JITYGGBXjit-idp',
         'idpDomain': 'perf255.com', 'totalUsers': 0},
        {'idpId': '6a6ab5e6-17e5-4c96-9bf5-872459018a44', 'idpDisplayName': 'ASTRA-OKTA-JIT75MQYjit-idp',
         'idpDomain': 'perf225.com', 'totalUsers': 0},
        {'idpId': '2789d415-eade-4063-8706-8eda1eb25b9a', 'idpDisplayName': 'ASTRA-OKTA-JITALPH1jit-idp',
         'idpDomain': 'perf345.com', 'totalUsers': 0},
        {'idpId': '559c9676-2e7c-4818-9352-56c4dca60932', 'idpDisplayName': 'ASTRA-OKTA-JITQGNFHjit-idp',
         'idpDomain': 'perf410.com', 'totalUsers': 0},
        {'idpId': 'd47915b3-8e6f-43fe-8da3-cdf2d4761a64', 'idpDisplayName': 'ASTRA-OKTA-JITYAUZJjit-idp',
         'idpDomain': 'perf403.com', 'totalUsers': 0},
        {'idpId': '4467799f-5c87-46bd-9492-d51e7ad417ae', 'idpDisplayName': 'ASTRA-OKTA-JIT1QCP2jit-idp',
         'idpDomain': 'perf437.com', 'totalUsers': 0},
        {'idpId': '841a966a-9852-4aa4-bd8f-cc13c58c45fc', 'idpDisplayName': 'ASTRA-OKTA-JITZTL8Ojit-idp',
         'idpDomain': 'perf12.com', 'totalUsers': 0},
        {'idpId': '3b691cfd-b682-4ac2-8592-3926d05e0943', 'idpDisplayName': 'ASTRA-OKTA-JIT58FFKjit-idp',
         'idpDomain': 'perf446.com', 'totalUsers': 0},
        {'idpId': '2874f906-23f2-40a8-bded-27833f6651f1', 'idpDisplayName': 'ASTRA-OKTA-JITC0A2Fjit-idp',
         'idpDomain': 'perf124.com', 'totalUsers': 0},
        {'idpId': '3197c961-5fa4-47a8-8ae7-b0fa0fd68658', 'idpDisplayName': 'ASTRA-OKTA-JITQ8107jit-idp',
         'idpDomain': 'perf119.com', 'totalUsers': 0},
        {'idpId': 'e13d3071-81ef-45bd-93e8-7482aa432e4b', 'idpDisplayName': 'ASTRA-OKTA-JIT4U282jit-idp',
         'idpDomain': 'perf383.com', 'totalUsers': 0},
        {'idpId': '8a0e6189-0791-4256-8468-1c258a3ac286', 'idpDisplayName': 'ASTRA-OKTA-JIT38O4Vjit-idp',
         'idpDomain': 'perf421.com', 'totalUsers': 0},
        {'idpId': '39fad40b-a1ab-44a7-90a1-a4eca1b866c7', 'idpDisplayName': 'ASTRA-OKTA-JITRRW0Gjit-idp',
         'idpDomain': 'perf487.com', 'totalUsers': 0},
        {'idpId': '2b80d952-e54c-4b0d-be29-e0c338e225fc', 'idpDisplayName': 'ASTRA-OKTA-JITA5JG0jit-idp',
         'idpDomain': 'perf188.com', 'totalUsers': 0},
        {'idpId': '369a9978-9381-4386-86e5-f4c61a3bf43c', 'idpDisplayName': 'ASTRA-OKTA-JITG4PU1jit-idp',
         'idpDomain': 'perf319.com', 'totalUsers': 0},
        {'idpId': '4820fff9-0e9a-4a3e-851d-8df99b4e3bc2', 'idpDisplayName': 'ASTRA-OKTA-JIT2GJ0Tjit-idp',
         'idpDomain': 'perf499.com', 'totalUsers': 0},
        {'idpId': '0a76ce4a-1505-48c7-ac49-32526b3271c0', 'idpDisplayName': 'ASTRA-OKTA-JITDX7L6jit-idp',
         'idpDomain': 'perf46.com', 'totalUsers': 0},
        {'idpId': 'd13849a3-c5ce-4825-a634-fd3efc59f11e', 'idpDisplayName': 'ASTRA-OKTA-JITQAM4Njit-idp',
         'idpDomain': 'perf83.com', 'totalUsers': 0},
        {'idpId': 'fe226bf5-217b-47aa-998e-b2e8ae65bbb2', 'idpDisplayName': 'ASTRA-OKTA-JITM7WWMjit-idp',
         'idpDomain': 'perf377.com', 'totalUsers': 0},
        {'idpId': 'd73da1e8-4e3e-4143-b2b4-d5dee026eac6', 'idpDisplayName': 'ASTRA-OKTA-JIT543WBjit-idp',
         'idpDomain': 'perf112.com', 'totalUsers': 0},
        {'idpId': '66a9e6ef-bac6-48e6-92f6-f8186fed14fa', 'idpDisplayName': 'ASTRA-OKTA-JIT79Q8Zjit-idp',
         'idpDomain': 'perf247.com', 'totalUsers': 0},
        {'idpId': '39d90f90-7e36-414e-adb2-679173325041', 'idpDisplayName': 'ASTRA-OKTA-JITA258Zjit-idp',
         'idpDomain': 'perf486.com', 'totalUsers': 0},
        {'idpId': 'af99e34f-5774-404a-b31c-eb2b00ae8591', 'idpDisplayName': 'ASTRA-OKTA-JIT2WC9Xjit-idp',
         'idpDomain': 'perf297.com', 'totalUsers': 0},
        {'idpId': '08241525-e662-4f08-8411-4dd71fc2f269', 'idpDisplayName': 'ASTRA-OKTA-JITB9XETjit-idp',
         'idpDomain': 'perf387.com', 'totalUsers': 0},
        {'idpId': 'bbd70d82-97c7-4c7b-99c5-c4933ec19bca', 'idpDisplayName': 'ASTRA-OKTA-JITHE9UNjit-idp',
         'idpDomain': 'perf90.com', 'totalUsers': 0},
        {'idpId': '39d5a15c-9637-4063-b9d1-5c8c4e4ca5b7', 'idpDisplayName': 'ASTRA-OKTA-JITMBKXYjit-idp',
         'idpDomain': 'perf465.com', 'totalUsers': 0},
        {'idpId': '5d660eb9-cd96-432d-9fe5-0601a00ead10', 'idpDisplayName': 'ASTRA-OKTA-JIT56AWOjit-idp',
         'idpDomain': 'perf461.com', 'totalUsers': 0},
        {'idpId': '06bc0ff1-dc27-47d8-8d0d-23c899d29fd1', 'idpDisplayName': 'ASTRA-OKTA-JITCKWXBjit-idp',
         'idpDomain': 'perf145.com', 'totalUsers': 0},
        {'idpId': '75db7ee3-c2ad-454d-9918-3aefcaa0b89a', 'idpDisplayName': 'ASTRA-OKTA-JITFMX30jit-idp',
         'idpDomain': 'perf26.com', 'totalUsers': 0},
        {'idpId': '27552ccf-da6a-4676-9dcd-be5bbb4fc4d4', 'idpDisplayName': 'ASTRA-OKTA-JITEUY4Rjit-idp',
         'idpDomain': 'perf161.com', 'totalUsers': 0},
        {'idpId': 'e77a55a6-3607-4e7c-b2e2-9bb7ea56c031', 'idpDisplayName': 'ASTRA-OKTA-JITBPDHRjit-idp',
         'idpDomain': 'perf82.com', 'totalUsers': 0},
        {'idpId': '414f1fb4-1295-4535-9a34-79d43cfb9801', 'idpDisplayName': 'ASTRA-OKTA-JITXS89Ljit-idp',
         'idpDomain': 'perf55.com', 'totalUsers': 0},
        {'idpId': 'eab9b2a5-a480-4699-a486-2f2f45e6f17c', 'idpDisplayName': 'ASTRA-OKTA-JITRKCBTjit-idp',
         'idpDomain': 'perf227.com', 'totalUsers': 0},
        {'idpId': 'dd7673ab-dfba-49eb-bc9c-4e2f035cd278', 'idpDisplayName': 'ASTRA-OKTA-JITVIMR9jit-idp',
         'idpDomain': 'perf14.com', 'totalUsers': 0},
        {'idpId': '1ea66956-d3dd-4491-bac4-03fe1ef3622c', 'idpDisplayName': 'ASTRA-OKTA-JIT95B76jit-idp',
         'idpDomain': 'perf102.com', 'totalUsers': 0},
        {'idpId': '7c3726ac-ed68-45b8-bec4-cf806684f1f6', 'idpDisplayName': 'ASTRA-OKTA-JIT4LX8Kjit-idp',
         'idpDomain': 'perf129.com', 'totalUsers': 0},
        {'idpId': '30c68483-a50d-4ac7-9a43-ca848f33a8a5', 'idpDisplayName': 'ASTRA-OKTA-JIT5T1PNjit-idp',
         'idpDomain': 'perf175.com', 'totalUsers': 0},
        {'idpId': '45da14b6-755c-4b68-b2ea-2c99e2473f10', 'idpDisplayName': 'ASTRA-OKTA-JIT76IRXjit-idp',
         'idpDomain': 'perf365.com', 'totalUsers': 0},
        {'idpId': '3ddef826-aff0-4622-8fd5-f6dda52933cc', 'idpDisplayName': 'ASTRA-OKTA-JITX4BPMjit-idp',
         'idpDomain': 'perf2.com', 'totalUsers': 0},
        {'idpId': '7a504a9a-857e-430c-898e-fd40150fb70d', 'idpDisplayName': 'ASTRA-OKTA-JITCBS4Ojit-idp',
         'idpDomain': 'perf367.com', 'totalUsers': 0},
        {'idpId': 'd8c8c85d-cee2-463b-9f77-245241d15122', 'idpDisplayName': 'ASTRA-OKTA-JITHE110jit-idp',
         'idpDomain': 'perf493.com', 'totalUsers': 0},
        {'idpId': '9134aa3c-dd44-4273-b462-ef7094e0ff4d', 'idpDisplayName': 'ASTRA-OKTA-JIT6R6QRjit-idp',
         'idpDomain': 'perf308.com', 'totalUsers': 0},
        {'idpId': 'c9b49523-615c-44c8-ae9c-bda9ad67d2bb', 'idpDisplayName': 'ASTRA-OKTA-JITUOGW6jit-idp',
         'idpDomain': 'perf200.com', 'totalUsers': 0},
        {'idpId': '32632161-ef10-400b-8613-7964a120a931', 'idpDisplayName': 'ASTRA-OKTA-JITEB1RGjit-idp',
         'idpDomain': 'perf201.com', 'totalUsers': 0},
        {'idpId': 'd280f0cb-22a2-4364-a3e7-64b73e64ba43', 'idpDisplayName': 'ASTRA-OKTA-JITV3QDXjit-idp',
         'idpDomain': 'perf267.com', 'totalUsers': 0},
        {'idpId': 'f3fd9e9d-dff7-443a-995a-15a85e31efa1', 'idpDisplayName': 'ASTRA-OKTA-JIT72E45jit-idp',
         'idpDomain': 'perf467.com', 'totalUsers': 0},
        {'idpId': 'b2db50a1-02f8-499b-a0f5-4848ccd4c8ab', 'idpDisplayName': 'ASTRA-OKTA-JITVTK64jit-idp',
         'idpDomain': 'perf398.com', 'totalUsers': 0},
        {'idpId': 'f2c07091-2d03-4a17-b65a-db028f927379', 'idpDisplayName': 'ASTRA-OKTA-JIT3JPQMjit-idp',
         'idpDomain': 'perf307.com', 'totalUsers': 0},
        {'idpId': '7b7f7771-30e4-4a94-bceb-e3e459f67836', 'idpDisplayName': 'ASTRA-OKTA-JITIO48Qjit-idp',
         'idpDomain': 'perf204.com', 'totalUsers': 0},
        {'idpId': 'ad74dd5c-6b46-48b1-89f2-17d8586835ba', 'idpDisplayName': 'ASTRA-OKTA-JITVANJDjit-idp',
         'idpDomain': 'perf42.com', 'totalUsers': 0},
        {'idpId': 'dc7981bf-4f0d-4cc9-8c3b-1fc1a160af0f', 'idpDisplayName': 'ASTRA-OKTA-JIT5SFFYjit-idp',
         'idpDomain': 'perf174.com', 'totalUsers': 0},
        {'idpId': 'cd91c301-190a-493d-a822-43e2063849c7', 'idpDisplayName': 'ASTRA-OKTA-JIT1RJF7jit-idp',
         'idpDomain': 'perf7.com', 'totalUsers': 0},
        {'idpId': '81e54535-7308-4903-baa5-c769f6810d20', 'idpDisplayName': 'ASTRA-OKTA-JIT40KN1jit-idp',
         'idpDomain': 'perf147.com', 'totalUsers': 0},
        {'idpId': 'ed7424bf-3042-4bc2-9c2b-93951ff9fa69', 'idpDisplayName': 'ASTRA-OKTA-JITIA5XVjit-idp',
         'idpDomain': 'perf394.com', 'totalUsers': 0},
        {'idpId': '8fd21f51-4d85-46a2-a590-68090ead39b1', 'idpDisplayName': 'ASTRA-OKTA-JITT21N2jit-idp',
         'idpDomain': 'perf73.com', 'totalUsers': 0},
        {'idpId': '2f7010c1-9082-4626-9db3-3792a65b7ea6', 'idpDisplayName': 'ASTRA-OKTA-JIT5DFKFjit-idp',
         'idpDomain': 'perf149.com', 'totalUsers': 0},
        {'idpId': '2fe2b1d2-21a7-4ccf-9de3-b3bf1ff26a6c', 'idpDisplayName': 'ASTRA-OKTA-JIT3CQRYjit-idp',
         'idpDomain': 'perf396.com', 'totalUsers': 0},
        {'idpId': '833fb685-7a99-47d7-812f-5aa634eba179', 'idpDisplayName': 'ASTRA-OKTA-JITBOH3Fjit-idp',
         'idpDomain': 'perf52.com', 'totalUsers': 0},
        {'idpId': 'b261ba72-0d13-49c3-8271-315f1186c175', 'idpDisplayName': 'ASTRA-OKTA-JITWDXT5jit-idp',
         'idpDomain': 'perf473.com', 'totalUsers': 0},
        {'idpId': 'b12ccd49-af4b-437e-95f6-edb550056f8d', 'idpDisplayName': 'ASTRA-OKTA-JITQE9DJjit-idp',
         'idpDomain': 'perf269.com', 'totalUsers': 0},
        {'idpId': 'eb3571ca-f0e7-4dda-9bc3-72f51a272d99', 'idpDisplayName': 'ASTRA-OKTA-JITNZ6AXjit-idp',
         'idpDomain': 'perf328.com', 'totalUsers': 0},
        {'idpId': '41c0f1a5-27ef-4f26-896e-9e98efab2525', 'idpDisplayName': 'ASTRA-OKTA-JITIWE3Tjit-idp',
         'idpDomain': 'perf463.com', 'totalUsers': 0},
        {'idpId': 'a1ef798e-94d0-4101-90e1-7ceb08468bcb', 'idpDisplayName': 'ASTRA-OKTA-JIT69J1Jjit-idp',
         'idpDomain': 'perf76.com', 'totalUsers': 0},
        {'idpId': 'bc4cc3d7-a013-428a-a16e-85ea5e591f4b', 'idpDisplayName': 'ASTRA-OKTA-JITOM580jit-idp',
         'idpDomain': 'perf324.com', 'totalUsers': 0},
        {'idpId': '3d5fbed3-5253-43fc-b63e-b7b8d176388c', 'idpDisplayName': 'ASTRA-OKTA-JITRMW0Tjit-idp',
         'idpDomain': 'perf248.com', 'totalUsers': 0},
        {'idpId': '59ef4fc7-58b3-4490-a5b9-9bf3a04f9af8', 'idpDisplayName': 'ASTRA-OKTA-JITTFCG3jit-idp',
         'idpDomain': 'perf11.com', 'totalUsers': 0},
        {'idpId': 'ac11742e-9c9f-4139-a564-6f9fffe83e75', 'idpDisplayName': 'ASTRA-OKTA-JITGKYALjit-idp',
         'idpDomain': 'perf458.com', 'totalUsers': 0},
        {'idpId': 'e9e7e33c-7f88-4002-901a-83ff5ecdfbb3', 'idpDisplayName': 'ASTRA-OKTA-JITAVMZSjit-idp',
         'idpDomain': 'perf104.com', 'totalUsers': 0},
        {'idpId': '82995dc5-911e-488c-8192-51ef708c626c', 'idpDisplayName': 'ASTRA-OKTA-JITFVYKUjit-idp',
         'idpDomain': 'perf490.com', 'totalUsers': 0},
        {'idpId': '43aeeb35-14cf-4175-9417-d29d90be9264', 'idpDisplayName': 'ASTRA-OKTA-JITJAHNPjit-idp',
         'idpDomain': 'perf343.com', 'totalUsers': 0},
        {'idpId': 'ccd046ea-c85b-461b-8348-5ebebaf7baaa', 'idpDisplayName': 'ASTRA-OKTA-JIT3SB7Vjit-idp',
         'idpDomain': 'perf246.com', 'totalUsers': 0},
        {'idpId': '8a04a034-81b1-4e70-977e-1673cee25b0d', 'idpDisplayName': 'ASTRA-OKTA-JITMW4HHjit-idp',
         'idpDomain': 'perf155.com', 'totalUsers': 0},
        {'idpId': '871e5b60-1b46-40ef-bbbb-2df0fe6330e1', 'idpDisplayName': 'ASTRA-OKTA-JITB86SPjit-idp',
         'idpDomain': 'perf444.com', 'totalUsers': 0},
        {'idpId': 'db4efeb5-27e1-48ee-a515-5fcf14eab611', 'idpDisplayName': 'ASTRA-OKTA-JITFIW0Jjit-idp',
         'idpDomain': 'perf165.com', 'totalUsers': 0},
        {'idpId': '31260a35-65cb-47c3-9002-e2b587b7841f', 'idpDisplayName': 'ASTRA-OKTA-JITCILJ5jit-idp',
         'idpDomain': 'perf53.com', 'totalUsers': 0},
        {'idpId': 'b977520a-92f5-4ad5-a0fa-5bf026530ea0', 'idpDisplayName': 'ASTRA-OKTA-JITPZGMPjit-idp',
         'idpDomain': 'perf433.com', 'totalUsers': 0},
        {'idpId': 'b8bcbd3f-6596-4241-82e5-e8701147b552', 'idpDisplayName': 'ASTRA-OKTA-JITUB778jit-idp',
         'idpDomain': 'perf285.com', 'totalUsers': 0},
        {'idpId': '917c1769-c7e8-4f88-bf48-6a9b690064a0', 'idpDisplayName': 'ASTRA-OKTA-JIT6HKRTjit-idp',
         'idpDomain': 'perf436.com', 'totalUsers': 0},
        {'idpId': '4a9ce5b8-8eee-4e13-9f04-af99f82c1d5a', 'idpDisplayName': 'ASTRA-OKTA-JIT4P2LFjit-idp',
         'idpDomain': 'perf289.com', 'totalUsers': 0},
        {'idpId': 'daa79080-2409-43a0-a4ab-840ae60c077c', 'idpDisplayName': 'ASTRA-OKTA-JITF5MIEjit-idp',
         'idpDomain': 'perf16.com', 'totalUsers': 0},
        {'idpId': '260353a7-000e-4cab-a2cc-48e628d068e0', 'idpDisplayName': 'ASTRA-OKTA-JIT0TC1Mjit-idp',
         'idpDomain': 'perf93.com', 'totalUsers': 0},
        {'idpId': 'c5679808-9eed-4e69-82cd-612eab233c98', 'idpDisplayName': 'ASTRA-OKTA-JIT16U8Ujit-idp',
         'idpDomain': 'perf388.com', 'totalUsers': 0},
        {'idpId': '191ac897-6889-4246-b9a0-82755729e95b', 'idpDisplayName': 'ASTRA-OKTA-JITC66G9jit-idp',
         'idpDomain': 'perf68.com', 'totalUsers': 0},
        {'idpId': '1a9cc179-e389-441a-8dbe-ba9932e73e2b', 'idpDisplayName': 'ASTRA-OKTA-JITGOTKGjit-idp',
         'idpDomain': 'perf372.com', 'totalUsers': 0},
        {'idpId': 'c1739df2-f2f4-4fc2-a186-c99bfbcd331d', 'idpDisplayName': 'ASTRA-OKTA-JITX5JALjit-idp',
         'idpDomain': 'perf266.com', 'totalUsers': 0},
        {'idpId': '3ecb3f46-b926-4427-82e9-3d9330deb081', 'idpDisplayName': 'ASTRA-OKTA-JITKO4FRjit-idp',
         'idpDomain': 'perf329.com', 'totalUsers': 0},
        {'idpId': 'ac89a5a1-61f0-455a-b0b0-636c2a2787b3', 'idpDisplayName': 'ASTRA-OKTA-JIT6BH1Djit-idp',
         'idpDomain': 'perf323.com', 'totalUsers': 0},
        {'idpId': 'fbec80db-92ff-4fda-b13a-ccbb479a7ae0', 'idpDisplayName': 'ASTRA-OKTA-JITV9TVEjit-idp',
         'idpDomain': 'perf226.com', 'totalUsers': 0},
        {'idpId': 'badee487-fb83-4b7d-b87c-a6a8c49b1476', 'idpDisplayName': 'ASTRA-OKTA-JITH51JMjit-idp',
         'idpDomain': 'perf182.com', 'totalUsers': 0},
        {'idpId': '9d90b566-1bda-415d-bcc4-3dec60d10774', 'idpDisplayName': 'ASTRA-OKTA-JIT8ARK8jit-idp',
         'idpDomain': 'perf258.com', 'totalUsers': 0},
        {'idpId': '5f350cbd-15a7-44bc-a5b1-096ebb9b77ec', 'idpDisplayName': 'ASTRA-OKTA-JITMBK4Ujit-idp',
         'idpDomain': 'perf378.com', 'totalUsers': 0},
        {'idpId': '10655b25-42c5-44cd-b7ac-7c316e68bca2', 'idpDisplayName': 'ASTRA-OKTA-JIT1A9TDjit-idp',
         'idpDomain': 'perf406.com', 'totalUsers': 0},
        {'idpId': 'c38521dd-7a32-421d-9cec-7367324995d4', 'idpDisplayName': 'ASTRA-OKTA-JIT7VWC5jit-idp',
         'idpDomain': 'perf452.com', 'totalUsers': 0},
        {'idpId': '70a4f774-da9d-4ace-a9de-8887dee1ff96', 'idpDisplayName': 'ASTRA-OKTA-JITQSPPZjit-idp',
         'idpDomain': 'perf352.com', 'totalUsers': 0},
        {'idpId': 'f87de3f6-f4e7-4d70-befd-2c29d36e25eb', 'idpDisplayName': 'ASTRA-OKTA-JIT4LFNPjit-idp',
         'idpDomain': 'perf494.com', 'totalUsers': 0},
        {'idpId': 'e9818fc7-f924-4d59-97c5-ab4771acc9e0', 'idpDisplayName': 'ASTRA-OKTA-JITBSO78jit-idp',
         'idpDomain': 'perf166.com', 'totalUsers': 0},
        {'idpId': '3b13b22c-5638-4d7b-8ecb-7c2d9dfff71f', 'idpDisplayName': 'ASTRA-OKTA-JIT81HS1jit-idp',
         'idpDomain': 'perf334.com', 'totalUsers': 0},
        {'idpId': 'b7f864c3-5d68-406d-b48a-415c068225ee', 'idpDisplayName': 'ASTRA-OKTA-JITQ82Q4jit-idp',
         'idpDomain': 'perf355.com', 'totalUsers': 0},
        {'idpId': '5e888937-23ee-49a6-ac06-b96b0bac7f46', 'idpDisplayName': 'ASTRA-OKTA-JITK3WG5jit-idp',
         'idpDomain': 'perf80.com', 'totalUsers': 0},
        {'idpId': '674589fb-e5a3-4c06-8fed-91d0d8031b11', 'idpDisplayName': 'ASTRA-OKTA-JITV2HLPjit-idp',
         'idpDomain': 'perf162.com', 'totalUsers': 0},
        {'idpId': 'fa950376-d98c-4b6f-8b43-75b05d17263d', 'idpDisplayName': 'ASTRA-OKTA-JITP4M0Wjit-idp',
         'idpDomain': 'perf17.com', 'totalUsers': 0},
        {'idpId': '49a9e376-c251-4fb5-b2e1-aaf5e9ce1113', 'idpDisplayName': 'ASTRA-OKTA-JIT1V2Y2jit-idp',
         'idpDomain': 'perf5.com', 'totalUsers': 0},
        {'idpId': '11ff1ebe-c5ce-404f-a95b-c9421b2965b8', 'idpDisplayName': 'ASTRA-OKTA-JIT4MINOjit-idp',
         'idpDomain': 'perf277.com', 'totalUsers': 0},
        {'idpId': '304a5e5d-8a36-4707-8bad-2e4097e58ce2', 'idpDisplayName': 'ASTRA-OKTA-JITSLDGJjit-idp',
         'idpDomain': 'perf252.com', 'totalUsers': 0},
        {'idpId': '0137eb7c-65f0-4c39-a696-cd962f48ebfa', 'idpDisplayName': 'ASTRA-OKTA-JITO0H8Ujit-idp',
         'idpDomain': 'perf265.com', 'totalUsers': 0},
        {'idpId': 'ac42e8e3-30d4-49d4-8f22-97c61356920e', 'idpDisplayName': 'ASTRA-OKTA-JITMQC6Ojit-idp',
         'idpDomain': 'perf198.com', 'totalUsers': 0},
        {'idpId': 'fd0bebdc-7004-40cf-99ba-11451abd5541', 'idpDisplayName': 'ASTRA-OKTA-JIT7MPM5jit-idp',
         'idpDomain': 'perf341.com', 'totalUsers': 0},
        {'idpId': '34112bf1-0d6f-47a0-8d66-0bb69a516d28', 'idpDisplayName': 'ASTRA-OKTA-JITPY5TQjit-idp',
         'idpDomain': 'perf170.com', 'totalUsers': 0},
        {'idpId': 'b139c6f6-99ce-464a-8c0b-bd35994b90b5', 'idpDisplayName': 'ASTRA-OKTA-JIT0D4E4jit-idp',
         'idpDomain': 'perf325.com', 'totalUsers': 0},
        {'idpId': '69067548-4128-49a8-86e6-de1992c93561', 'idpDisplayName': 'ASTRA-OKTA-JITJV1N5jit-idp',
         'idpDomain': 'perf337.com', 'totalUsers': 0},
        {'idpId': '1fddd977-291c-4b9d-986b-1a4e55e112c0', 'idpDisplayName': 'ASTRA-OKTA-JITROYOTjit-idp',
         'idpDomain': 'perf77.com', 'totalUsers': 0},
        {'idpId': '08f89520-0538-4069-9801-d18cab298316', 'idpDisplayName': 'ASTRA-OKTA-JITNM79Fjit-idp',
         'idpDomain': 'perf32.com', 'totalUsers': 0},
        {'idpId': '9fa73be7-a9d5-45a5-a3d3-c25f575a5186', 'idpDisplayName': 'ASTRA-OKTA-JITNQXIOjit-idp',
         'idpDomain': 'perf279.com', 'totalUsers': 0},
        {'idpId': '16f40485-5e44-439b-927b-d3dba8117397', 'idpDisplayName': 'ASTRA-OKTA-JITWOPSFjit-idp',
         'idpDomain': 'perf59.com', 'totalUsers': 0},
        {'idpId': '26760d78-ad18-47ad-a9c9-28e7bac5f153', 'idpDisplayName': 'ASTRA-OKTA-JITODSETjit-idp',
         'idpDomain': 'perf438.com', 'totalUsers': 0},
        {'idpId': '36d37da7-8dc1-494d-8092-fa3dae63d6b6', 'idpDisplayName': 'ASTRA-OKTA-JITBBCG3jit-idp',
         'idpDomain': 'perf249.com', 'totalUsers': 0},
        {'idpId': '294e21aa-ff6c-4997-b4ea-bfccda85f016', 'idpDisplayName': 'ASTRA-OKTA-JITU0YVYjit-idp',
         'idpDomain': 'perf181.com', 'totalUsers': 0},
        {'idpId': '54daf154-865e-4fac-a16c-711e2ae4de58', 'idpDisplayName': 'ASTRA-OKTA-JITVFBPQjit-idp',
         'idpDomain': 'perf314.com', 'totalUsers': 0},
        {'idpId': '45788a8c-2bf7-41e7-97ae-4a0bde710c34', 'idpDisplayName': 'ASTRA-OKTA-JITKNZHZjit-idp',
         'idpDomain': 'perf206.com', 'totalUsers': 0},
        {'idpId': 'eb31eda7-9924-4390-ac80-8eccc0f0de89', 'idpDisplayName': 'ASTRA-OKTA-JITVUJQ6jit-idp',
         'idpDomain': 'perf229.com', 'totalUsers': 0},
        {'idpId': 'ea3ebba0-100b-40cc-8dad-b0e989f5e6a6', 'idpDisplayName': 'ASTRA-OKTA-JITV16UHjit-idp',
         'idpDomain': 'perf15.com', 'totalUsers': 0},
        {'idpId': '1dc2c014-5b50-4bb1-aae3-30162c7dd1be', 'idpDisplayName': 'ASTRA-OKTA-JITLBNFIjit-idp',
         'idpDomain': 'perf287.com', 'totalUsers': 0},
        {'idpId': '3358e66a-c221-4467-9261-66462b288a0f', 'idpDisplayName': 'ASTRA-OKTA-JIT2CJZ4jit-idp',
         'idpDomain': 'perf169.com', 'totalUsers': 0},
        {'idpId': '2379b960-d4fb-451b-b0ac-4eb2631409d4', 'idpDisplayName': 'ASTRA-OKTA-JITAIFIPjit-idp',
         'idpDomain': 'perf131.com', 'totalUsers': 0},
        {'idpId': 'f144f419-59eb-45be-87fb-b21037905bbc', 'idpDisplayName': 'ASTRA-OKTA-JITAOCFFjit-idp',
         'idpDomain': 'perf69.com', 'totalUsers': 0},
        {'idpId': '68c5c498-0270-407f-9cec-f6e5de7f8284', 'idpDisplayName': 'ASTRA-OKTA-JITVH6ANjit-idp',
         'idpDomain': 'perf168.com', 'totalUsers': 0},
        {'idpId': 'b1265e7a-f6b8-4daf-9a9c-983437406849', 'idpDisplayName': 'ASTRA-OKTA-JITC8VTNjit-idp',
         'idpDomain': 'perf243.com', 'totalUsers': 0},
        {'idpId': '7ebd6b53-a50e-4b6c-ac58-51bf4db375ff', 'idpDisplayName': 'ASTRA-OKTA-JIT7EQHVjit-idp',
         'idpDomain': 'perf386.com', 'totalUsers': 0},
        {'idpId': '0941901f-7538-46c8-a6b9-82d8a29e6192', 'idpDisplayName': 'ASTRA-OKTA-JITXZMM0jit-idp',
         'idpDomain': 'perf339.com', 'totalUsers': 0},
        {'idpId': '1149b60b-4e4b-4b17-9ad5-813e74a080ee', 'idpDisplayName': 'ASTRA-OKTA-JITFEWA7jit-idp',
         'idpDomain': 'perf153.com', 'totalUsers': 0},
        {'idpId': '6620c19c-4cdc-45e6-a788-7c857e69db2d', 'idpDisplayName': 'ASTRA-OKTA-JITYYE1Wjit-idp',
         'idpDomain': 'perf74.com', 'totalUsers': 0},
        {'idpId': '33b49f00-30d0-4b0c-97a7-f3ff72c0f710', 'idpDisplayName': 'ASTRA-OKTA-JIT5UPHXjit-idp',
         'idpDomain': 'perf424.com', 'totalUsers': 0},
        {'idpId': 'f3f366b4-de1e-4b19-a08e-ea91b69e4bdc', 'idpDisplayName': 'ASTRA-OKTA-JIT8007Gjit-idp',
         'idpDomain': 'perf280.com', 'totalUsers': 0},
        {'idpId': 'fb0b65cf-26a1-40c3-83cf-cd91ac4ef57f', 'idpDisplayName': 'ASTRA-OKTA-JITRG792jit-idp',
         'idpDomain': 'perf301.com', 'totalUsers': 0},
        {'idpId': '3fcf5bb0-b82d-4986-8667-4987b1c84c4a', 'idpDisplayName': 'ASTRA-OKTA-JITVBN4Xjit-idp',
         'idpDomain': 'perf335.com', 'totalUsers': 0},
        {'idpId': '56bc2e75-b403-45e1-bc82-a8a4f4e95dbf', 'idpDisplayName': 'ASTRA-OKTA-JIT77E1Xjit-idp',
         'idpDomain': 'perf138.com', 'totalUsers': 0},
        {'idpId': '808d096e-a84d-4369-8578-ea6e6687f014', 'idpDisplayName': 'ASTRA-OKTA-JIT0AFT1jit-idp',
         'idpDomain': 'perf211.com', 'totalUsers': 0},
        {'idpId': 'ae72a8e4-4e09-455c-9d54-d898fba1f287', 'idpDisplayName': 'ASTRA-OKTA-JITA6EP9jit-idp',
         'idpDomain': 'trial1.com', 'totalUsers': 0},
        {'idpId': 'd4cfefdc-8239-4182-8f12-b56e2b7cdd70', 'idpDisplayName': 'ASTRA-OKTA-JITVVZATjit-idp',
         'idpDomain': 'perf442.com', 'totalUsers': 0},
        {'idpId': '64375287-f86d-4de5-a61d-dfaf7f731e08', 'idpDisplayName': 'ASTRA-OKTA-JITZ9HWYjit-idp',
         'idpDomain': 'perf353.com', 'totalUsers': 0},
        {'idpId': '837272df-0fc0-49ef-9d5f-03e96c7553b0', 'idpDisplayName': 'ASTRA-OKTA-JIT7FK6Vjit-idp',
         'idpDomain': 'perf286.com', 'totalUsers': 0},
        {'idpId': '39245e54-5aae-4071-aeb3-16cd9fe2c634', 'idpDisplayName': 'ASTRA-OKTA-JIT7I5O6jit-idp',
         'idpDomain': 'perf105.com', 'totalUsers': 0},
        {'idpId': '29a347c7-8ffa-4b3e-b621-3d59bc6dbf67', 'idpDisplayName': 'ASTRA-OKTA-JITN9DENjit-idp',
         'idpDomain': 'perf114.com', 'totalUsers': 0},
        {'idpId': 'c4458690-8b02-4f88-9504-170d5d24b857', 'idpDisplayName': 'ASTRA-OKTA-JITHN3CUjit-idp',
         'idpDomain': 'perf37.com', 'totalUsers': 0},
        {'idpId': '6e032539-980e-425f-baab-3c9de8a961a0', 'idpDisplayName': 'ASTRA-OKTA-JITU1UI6jit-idp',
         'idpDomain': 'perf251.com', 'totalUsers': 0},
        {'idpId': 'b90cc08e-7e9b-429e-824f-c7dcd0787f48', 'idpDisplayName': 'ASTRA-OKTA-JITQO6FBjit-idp',
         'idpDomain': 'perf312.com', 'totalUsers': 0},
        {'idpId': '1c1d8fe7-2f05-487e-9235-d51ce2711853', 'idpDisplayName': 'ASTRA-OKTA-JIT7H9RIjit-idp',
         'idpDomain': 'perf423.com', 'totalUsers': 0},
        {'idpId': '7040ae94-c662-4ebf-82e3-37055c55ec4a', 'idpDisplayName': 'ASTRA-OKTA-JITABSWGjit-idp',
         'idpDomain': 'perf130.com', 'totalUsers': 0},
        {'idpId': '479f7a2b-d463-41a3-824a-119759a524b7', 'idpDisplayName': 'ASTRA-OKTA-JITR7MEFjit-idp',
         'idpDomain': 'perf98.com', 'totalUsers': 0},
        {'idpId': 'b2714f96-052f-404b-b6f2-39943ad008c9', 'idpDisplayName': 'ASTRA-OKTA-JITOCC8Bjit-idp',
         'idpDomain': 'perf163.com', 'totalUsers': 0},
        {'idpId': 'c5f9b733-32c9-476d-87db-c8a1645eb4d2', 'idpDisplayName': 'ASTRA-OKTA-JITMTFQIjit-idp',
         'idpDomain': 'perf78.com', 'totalUsers': 0},
        {'idpId': 'b24a6e99-1095-4b11-acbb-e2603b878135', 'idpDisplayName': 'ASTRA-OKTA-JITG3844jit-idp',
         'idpDomain': 'perf50.com', 'totalUsers': 0},
        {'idpId': '38d2ca0e-3571-41d8-b7df-296939513bec', 'idpDisplayName': 'ASTRA-OKTA-JITZD365jit-idp',
         'idpDomain': 'perf368.com', 'totalUsers': 0},
        {'idpId': 'bf32f1cb-6045-4aaf-a451-c6450ba03f40', 'idpDisplayName': 'ASTRA-OKTA-JITR88A7jit-idp',
         'idpDomain': 'perf63.com', 'totalUsers': 0},
        {'idpId': '9e1beb8d-eab2-41cd-ac30-51fe5910a7b5', 'idpDisplayName': 'ASTRA-OKTA-JITIIW99jit-idp',
         'idpDomain': 'perf152.com', 'totalUsers': 0},
        {'idpId': '276402ea-1bf0-446b-866f-a92d4db7df58', 'idpDisplayName': 'ASTRA-OKTA-JITENEYQjit-idp',
         'idpDomain': 'perf315.com', 'totalUsers': 0},
        {'idpId': '79c30afa-52f9-44ec-9227-1f191da1027a', 'idpDisplayName': 'ASTRA-OKTA-JITSXX21jit-idp',
         'idpDomain': 'perf281.com', 'totalUsers': 0},
        {'idpId': '3b3ccf91-891d-41b2-b906-bcbb7f72df18', 'idpDisplayName': 'ASTRA-OKTA-JITHPYEYjit-idp',
         'idpDomain': 'perf218.com', 'totalUsers': 0},
        {'idpId': '06cb3a8a-74d0-4a64-ac3a-df41d7c47a86', 'idpDisplayName': 'ASTRA-OKTA-JIT1LKPBjit-idp',
         'idpDomain': 'perf66.com', 'totalUsers': 0},
        {'idpId': 'e3bc8a64-a3b5-429a-a5a5-b01ce2a755e3', 'idpDisplayName': 'ASTRA-OKTA-JITPMPQKjit-idp',
         'idpDomain': 'perf350.com', 'totalUsers': 0},
        {'idpId': 'efd70c50-6ec4-4e2b-b709-f0b726b77478', 'idpDisplayName': 'ASTRA-OKTA-JITT8QYMjit-idp',
         'idpDomain': 'perf64.com', 'totalUsers': 0},
        {'idpId': '009533fe-ba71-4ee0-8705-292641735e0c', 'idpDisplayName': 'ASTRA-OKTA-JIT6Z5EYjit-idp',
         'idpDomain': 'perf484.com', 'totalUsers': 0},
        {'idpId': '63c7a2fb-c46e-477c-a287-7366b9d57a76', 'idpDisplayName': 'ASTRA-OKTA-JITUDT2Djit-idp',
         'idpDomain': 'perf488.com', 'totalUsers': 0},
        {'idpId': '5f69078a-3c65-41cf-b82c-b8ab02f8b980', 'idpDisplayName': 'ASTRA-OKTA-JIT6UAOJjit-idp',
         'idpDomain': 'perf282.com', 'totalUsers': 0},
        {'idpId': 'aaaba1e3-9de5-4445-836a-f048efad5566', 'idpDisplayName': 'ASTRA-OKTA-JITJWYRUjit-idp',
         'idpDomain': 'perf482.com', 'totalUsers': 0},
        {'idpId': '92e7c70a-a679-445c-9fde-c0fd8f4a7b8b', 'idpDisplayName': 'ASTRA-OKTA-JITAZHQ8jit-idp',
         'idpDomain': 'perf208.com', 'totalUsers': 0},
        {'idpId': 'ac85dac5-5bbe-4017-a4c6-8e7bb7ab25ad', 'idpDisplayName': 'ASTRA-OKTA-JITDSUXIjit-idp',
         'idpDomain': 'perf132.com', 'totalUsers': 0},
        {'idpId': '76a03ede-efa4-4f01-9e72-e4feb191a05d', 'idpDisplayName': 'ASTRA-OKTA-JIT0666Zjit-idp',
         'idpDomain': 'perf224.com', 'totalUsers': 0},
        {'idpId': '24e861b4-30c9-42ec-b855-901a3abb621d', 'idpDisplayName': 'ASTRA-OKTA-JITHT323jit-idp',
         'idpDomain': 'perf489.com', 'totalUsers': 0},
        {'idpId': '8fbb4f75-eaa4-4d2c-b6ad-a0dcef69d183', 'idpDisplayName': 'ASTRA-OKTA-JITGNL67jit-idp',
         'idpDomain': 'perf202.com', 'totalUsers': 0},
        {'idpId': '247ea887-d21b-4ab6-b584-c879e4e00afa', 'idpDisplayName': 'ASTRA-OKTA-JITY1HHBjit-idp',
         'idpDomain': 'perf65.com', 'totalUsers': 0},
        {'idpId': '939a5606-80ba-474e-84fa-0349f22a370b', 'idpDisplayName': 'ASTRA-OKTA-JITY1A9Xjit-idp',
         'idpDomain': 'perf294.com', 'totalUsers': 0},
        {'idpId': 'a21d377b-a63b-4df0-80f2-58e5946b14a2', 'idpDisplayName': 'ASTRA-OKTA-JITQ1N6Ojit-idp',
         'idpDomain': 'perf262.com', 'totalUsers': 0},
        {'idpId': 'deab5b43-415c-4a47-b375-b0b15c7bbb1d', 'idpDisplayName': 'ASTRA-OKTA-JIT65J5Wjit-idp',
         'idpDomain': 'perf189.com', 'totalUsers': 0},
        {'idpId': '49ece76d-8588-461e-9efd-a81ef7e53323', 'idpDisplayName': 'ASTRA-OKTA-JITBZNPLjit-idp',
         'idpDomain': 'perf330.com', 'totalUsers': 0},
        {'idpId': '34c55a77-01b8-4c33-ae45-39867d60c101', 'idpDisplayName': 'ASTRA-OKTA-JITM1V2Ajit-idp',
         'idpDomain': 'perf106.com', 'totalUsers': 0},
        {'idpId': '978002e6-5fae-4254-81f5-bc660f08fe6e', 'idpDisplayName': 'ASTRA-OKTA-JITXOLJNjit-idp',
         'idpDomain': 'perf150.com', 'totalUsers': 0},
        {'idpId': '239a62a3-d2b2-4657-9e67-0376053842bb', 'idpDisplayName': 'ASTRA-OKTA-JITT7KQSjit-idp',
         'idpDomain': 'perf56.com', 'totalUsers': 0},
        {'idpId': '71b09270-3701-4ada-b4a9-9dcca1d7165d', 'idpDisplayName': 'ASTRA-OKTA-JIT8LCR8jit-idp',
         'idpDomain': 'perf300.com', 'totalUsers': 0},
        {'idpId': '2faf868d-5eee-49b7-8bdf-33242bd7bba5', 'idpDisplayName': 'ASTRA-OKTA-JITFBN1Ijit-idp',
         'idpDomain': 'perf28.com', 'totalUsers': 0},
        {'idpId': '3aacabbe-e079-4283-bbb0-0feed79652e7', 'idpDisplayName': 'ASTRA-OKTA-JITS1W7Bjit-idp',
         'idpDomain': 'perf186.com', 'totalUsers': 0},
        {'idpId': '3079f273-1392-40c7-97bd-95cf3594611e', 'idpDisplayName': 'ASTRA-OKTA-JITWNV04jit-idp',
         'idpDomain': 'perf483.com', 'totalUsers': 0},
        {'idpId': '86575aa8-d7cf-4266-bc39-82badd34307c', 'idpDisplayName': 'ASTRA-OKTA-JITSGII3jit-idp',
         'idpDomain': 'perf309.com', 'totalUsers': 0},
        {'idpId': '9e92cb3a-9099-44f7-bcf9-1258b3c91183', 'idpDisplayName': 'ASTRA-OKTA-JITA0FVXjit-idp',
         'idpDomain': 'perf30.com', 'totalUsers': 0},
        {'idpId': 'd4503a91-1708-4a9e-a38f-56173acec2c9', 'idpDisplayName': 'ASTRA-OKTA-JITNBRZQjit-idp',
         'idpDomain': 'perf139.com', 'totalUsers': 0},
        {'idpId': 'a2c5b22e-1dcb-4569-902a-ffc94a0db961', 'idpDisplayName': 'ASTRA-OKTA-JITWJVAHjit-idp',
         'idpDomain': 'perf414.com', 'totalUsers': 0},
        {'idpId': 'c9cfdfb6-20fb-4ede-b431-8f71d89694f0', 'idpDisplayName': 'ASTRA-OKTA-JITINXNZjit-idp',
         'idpDomain': 'perf449.com', 'totalUsers': 0},
        {'idpId': '5d6cc945-f9cf-4860-ba69-a41e8ee5588b', 'idpDisplayName': 'ASTRA-OKTA-JITV21IJjit-idp',
         'idpDomain': 'perf361.com', 'totalUsers': 0},
        {'idpId': 'd5b1cc3f-f9f3-44f7-90e2-8cceb4374f70', 'idpDisplayName': 'ASTRA-OKTA-JITDAW81jit-idp',
         'idpDomain': 'perf346.com', 'totalUsers': 0},
        {'idpId': 'e6981097-8a79-4f80-88f8-33898212ac2b', 'idpDisplayName': 'ASTRA-OKTA-JITCAQDAjit-idp',
         'idpDomain': 'perf110.com', 'totalUsers': 0},
        {'idpId': 'cfe34c63-9def-4819-ae7f-026560483522', 'idpDisplayName': 'ASTRA-OKTA-JITJUCY0jit-idp',
         'idpDomain': 'perf293.com', 'totalUsers': 0},
        {'idpId': '37642aa8-01b9-40a9-843a-f6a17838b9c0', 'idpDisplayName': 'ASTRA-OKTA-JITWS8BQjit-idp',
         'idpDomain': 'perf440.com', 'totalUsers': 0},
        {'idpId': '29adc93f-9d67-47c8-9529-6cf5bb0a02e4', 'idpDisplayName': 'ASTRA-OKTA-JIT4YW3Vjit-idp',
         'idpDomain': 'perf390.com', 'totalUsers': 0},
        {'idpId': '85e08a25-f20b-45be-95bb-0571c953cc0a', 'idpDisplayName': 'ASTRA-OKTA-JITT8F74jit-idp',
         'idpDomain': 'perf235.com', 'totalUsers': 0},
        {'idpId': 'd023460f-e09a-4769-8d4a-7849778a0a8b', 'idpDisplayName': 'ASTRA-OKTA-JITDCFK1jit-idp',
         'idpDomain': 'perf356.com', 'totalUsers': 0},
        {'idpId': 'fd15efe1-ceb4-4065-92a8-c9281f8f363a', 'idpDisplayName': 'ASTRA-OKTA-JITOVJ06jit-idp',
         'idpDomain': 'perf233.com', 'totalUsers': 0},
        {'idpId': 'fb3b0832-489a-48bd-b0c6-1af5c4f3de4a', 'idpDisplayName': 'ASTRA-OKTA-JITOR6GIjit-idp',
         'idpDomain': 'perf71.com', 'totalUsers': 0},
        {'idpId': 'a3206a1e-0620-4693-a368-78a72ea88b14', 'idpDisplayName': 'ASTRA-OKTA-JIT3401Njit-idp',
         'idpDomain': 'perf331.com', 'totalUsers': 0},
        {'idpId': '92007bdd-b9a3-4d04-8bee-148206719299', 'idpDisplayName': 'ASTRA-OKTA-JITEZ94Ejit-idp',
         'idpDomain': 'perf113.com', 'totalUsers': 0},
        {'idpId': 'f77218b5-7e34-4ae4-808a-3616c1f99136', 'idpDisplayName': 'ASTRA-OKTA-JITMLSRFjit-idp',
         'idpDomain': 'perf454.com', 'totalUsers': 0},
        {'idpId': '8159ef2c-db87-4de0-8cba-73aaf335a709', 'idpDisplayName': 'ASTRA-OKTA-JIT87CI9jit-idp',
         'idpDomain': 'perf40.com', 'totalUsers': 0},
        {'idpId': '1b3695ca-d3e8-4c26-874f-c912fe50983c', 'idpDisplayName': 'ASTRA-OKTA-JIT2G83Ojit-idp',
         'idpDomain': 'perf122.com', 'totalUsers': 0},
        {'idpId': '604f63a9-d681-403b-9fe0-20471cb27495', 'idpDisplayName': 'ASTRA-OKTA-JITQVZD2jit-idp',
         'idpDomain': 'perf400.com', 'totalUsers': 0},
        {'idpId': 'c1d5291e-ecae-4beb-af86-ac41010628c9', 'idpDisplayName': 'ASTRA-OKTA-JIT1642Ljit-idp',
         'idpDomain': 'perf92.com', 'totalUsers': 0},
        {'idpId': '881f85b4-68e1-4b2f-947b-127b7dc48108', 'idpDisplayName': 'ASTRA-OKTA-JITD05OYjit-idp',
         'idpDomain': 'perf272.com', 'totalUsers': 0},
        {'idpId': '240af17c-1a1f-4537-b445-d540d62c8348', 'idpDisplayName': 'ASTRA-OKTA-JITFRF4Zjit-idp',
         'idpDomain': 'perf96.com', 'totalUsers': 0},
        {'idpId': 'cfb83a5d-79a6-4d73-8504-7691cdce6d7a', 'idpDisplayName': 'ASTRA-OKTA-JITYU5G0jit-idp',
         'idpDomain': 'perf474.com', 'totalUsers': 0},
        {'idpId': '826a7edc-1ca4-4288-a96b-65ea999895cc', 'idpDisplayName': 'ASTRA-OKTA-JIT0UGIGjit-idp',
         'idpDomain': 'perf344.com', 'totalUsers': 0},
        {'idpId': '2be1c04d-5668-4dd2-a536-a7ae229a9b48', 'idpDisplayName': 'ASTRA-OKTA-JITJ7K43jit-idp',
         'idpDomain': 'perf278.com', 'totalUsers': 0},
        {'idpId': 'fb0de401-6870-47fd-9a86-632d763a53e0', 'idpDisplayName': 'ASTRA-OKTA-JIT0TTRGjit-idp',
         'idpDomain': 'perf362.com', 'totalUsers': 0},
        {'idpId': '323cae3d-2dad-426f-b184-40b432168edf', 'idpDisplayName': 'ASTRA-OKTA-JITNZ30Ajit-idp',
         'idpDomain': 'perf427.com', 'totalUsers': 0},
        {'idpId': '57b1ead9-7cbd-43ad-92e6-5f4f57db5fe2', 'idpDisplayName': 'ASTRA-OKTA-JITR4WPGjit-idp',
         'idpDomain': 'perf115.com', 'totalUsers': 0},
        {'idpId': 'a3c509f2-f8fd-4320-84c5-ab2a70d6af1b', 'idpDisplayName': 'ASTRA-OKTA-JITDZDZDjit-idp',
         'idpDomain': 'perf239.com', 'totalUsers': 0},
        {'idpId': 'b486e99e-6dd2-431a-8ad5-699ee3fef212', 'idpDisplayName': 'ASTRA-OKTA-JITWUIFHjit-idp',
         'idpDomain': 'perf495.com', 'totalUsers': 0},
        {'idpId': 'bf29a71d-d29e-4281-87e9-a594cb0b8e5a', 'idpDisplayName': 'ASTRA-OKTA-JITICHKJjit-idp',
         'idpDomain': 'perf448.com', 'totalUsers': 0},
        {'idpId': 'f0e2a7a0-8224-427e-a80c-8fc41e606543', 'idpDisplayName': 'ASTRA-OKTA-JIT1FK9Yjit-idp',
         'idpDomain': 'perf351.com', 'totalUsers': 0},
        {'idpId': '78dc0f51-6199-4a38-a55d-0b2849316641', 'idpDisplayName': 'ASTRA-OKTA-JITKOVLRjit-idp',
         'idpDomain': 'perf375.com', 'totalUsers': 0},
        {'idpId': 'ab3ecc11-309f-4a84-bed9-33985b3507ed', 'idpDisplayName': 'ASTRA-OKTA-JIT1SFLYjit-idp',
         'idpDomain': 'perf45.com', 'totalUsers': 0},
        {'idpId': '68b4e1c2-e1ce-4900-a5c6-21f24a51fcf5', 'idpDisplayName': 'ASTRA-OKTA-JITK3JSVjit-idp',
         'idpDomain': 'perf384.com', 'totalUsers': 0},
        {'idpId': '8cd29acd-f1cd-46a1-ae28-7b48b31e3bab', 'idpDisplayName': 'ASTRA-OKTA-JITQZVOCjit-idp',
         'idpDomain': 'perf498.com', 'totalUsers': 0},
        {'idpId': 'fb2a39d7-5b4b-4601-a624-f7028e21e847', 'idpDisplayName': 'ASTRA-OKTA-JITX7Z85jit-idp',
         'idpDomain': 'perf405.com', 'totalUsers': 0},
        {'idpId': '752cd0d2-d7b4-4ed2-829e-9dc4f8f72c1e', 'idpDisplayName': 'ASTRA-OKTA-JITE4I3Sjit-idp',
         'idpDomain': 'perf468.com', 'totalUsers': 0},
        {'idpId': '26a5da8e-b5f2-4952-b07d-d15c19745dd1', 'idpDisplayName': 'ASTRA-OKTA-JITRO32Kjit-idp',
         'idpDomain': 'perf310.com', 'totalUsers': 0},
        {'idpId': 'fbbe4875-879b-41ad-bb27-5884865f0045', 'idpDisplayName': 'ASTRA-OKTA-JITXOUREjit-idp',
         'idpDomain': 'perf60.com', 'totalUsers': 0},
        {'idpId': 'e41ad0be-2635-4570-b964-4c13e097f353', 'idpDisplayName': 'ASTRA-OKTA-JITIYDJJjit-idp',
         'idpDomain': 'perf434.com', 'totalUsers': 0},
        {'idpId': 'e51a9cff-8017-4599-b395-24713a680b1a', 'idpDisplayName': 'ASTRA-OKTA-JITI1YB4jit-idp',
         'idpDomain': 'perf380.com', 'totalUsers': 0},
        {'idpId': 'd8847770-aa25-4685-86d7-b4460657e722', 'idpDisplayName': 'ASTRA-OKTA-JITJ249Bjit-idp',
         'idpDomain': 'perf231.com', 'totalUsers': 0},
        {'idpId': 'df163524-0631-4eb5-9dbe-175a8642cb08', 'idpDisplayName': 'ASTRA-OKTA-JIT90MCYjit-idp',
         'idpDomain': 'perf134.com', 'totalUsers': 0},
        {'idpId': '3b056079-297d-47a3-b4bc-aa994ee2950c', 'idpDisplayName': 'ASTRA-OKTA-JITOY16Tjit-idp',
         'idpDomain': 'perf192.com', 'totalUsers': 0},
        {'idpId': 'f3dcea3c-5156-40bb-b3c9-5235d8f76672', 'idpDisplayName': 'ASTRA-OKTA-JIT68XRHjit-idp',
         'idpDomain': 'perf419.com', 'totalUsers': 0},
        {'idpId': 'f00255ea-0561-4c5b-bff2-ba7892f8f755', 'idpDisplayName': 'ASTRA-OKTA-JITB32U0jit-idp',
         'idpDomain': 'perf260.com', 'totalUsers': 0},
        {'idpId': '41dbeb55-783f-4d02-a979-69604b8d7167', 'idpDisplayName': 'ASTRA-OKTA-JITABD6Kjit-idp',
         'idpDomain': 'perf39.com', 'totalUsers': 0},
        {'idpId': 'b344899a-d474-4cb0-801d-c33055022936', 'idpDisplayName': 'ASTRA-OKTA-JITT4BATjit-idp',
         'idpDomain': 'perf426.com', 'totalUsers': 0},
        {'idpId': '903268ac-88d6-4f94-a294-a74e6a5dbcb0', 'idpDisplayName': 'ASTRA-OKTA-JITHMGX2jit-idp',
         'idpDomain': 'perf318.com', 'totalUsers': 0},
        {'idpId': '81ca67d1-c5d6-4972-b3fc-f62eac712eb7', 'idpDisplayName': 'ASTRA-OKTA-JITGA5TMjit-idp',
         'idpDomain': 'perf306.com', 'totalUsers': 0},
        {'idpId': 'c4e8b580-cd13-4ee0-9469-a9f2a92df11f', 'idpDisplayName': 'ASTRA-OKTA-JITGR8I5jit-idp',
         'idpDomain': 'perf374.com', 'totalUsers': 0},
        {'idpId': '8e7cba8a-539e-495c-bb67-8c409c2c074f', 'idpDisplayName': 'ASTRA-OKTA-JITIJMHXjit-idp',
         'idpDomain': 'perf58.com', 'totalUsers': 0},
        {'idpId': '2cde1a99-a8d5-43c4-9198-fc031f6c500f', 'idpDisplayName': 'ASTRA-OKTA-JITQFPHMjit-idp',
         'idpDomain': 'perf158.com', 'totalUsers': 0},
        {'idpId': 'f0cd467c-47d7-4923-8abb-ac6868eee206', 'idpDisplayName': 'ASTRA-OKTA-JITO0Q6Cjit-idp',
         'idpDomain': 'perf210.com', 'totalUsers': 0},
        {'idpId': 'e51161c4-3134-4bf4-aba4-15c24c6c92bb', 'idpDisplayName': 'ASTRA-OKTA-JITOLZPIjit-idp',
         'idpDomain': 'perf199.com', 'totalUsers': 0},
        {'idpId': '03f4ee4b-60af-4c55-b2a0-16754c1fbb40', 'idpDisplayName': 'ASTRA-OKTA-JITHD1OUjit-idp',
         'idpDomain': 'perf21.com', 'totalUsers': 0},
        {'idpId': '73084222-1fca-4c44-9450-5dbf9f9f5041', 'idpDisplayName': 'ASTRA-OKTA-JITRHA1Pjit-idp',
         'idpDomain': 'perf23.com', 'totalUsers': 0},
        {'idpId': 'b6977a12-ed0a-4843-8e2f-0593a7a5d1a0', 'idpDisplayName': 'ASTRA-OKTA-JIT0C2R9jit-idp',
         'idpDomain': 'perf404.com', 'totalUsers': 0},
        {'idpId': '6e30235b-70d9-4abd-85fc-f9af6c7d5f7c', 'idpDisplayName': 'ASTRA-OKTA-JITWZHI5jit-idp',
         'idpDomain': 'perf217.com', 'totalUsers': 0},
        {'idpId': '36a7dfbd-8f7d-406e-9428-da5d19d16839', 'idpDisplayName': 'ASTRA-OKTA-JITONK97jit-idp',
         'idpDomain': 'perf126.com', 'totalUsers': 0},
        {'idpId': '02f04520-51bd-466c-a6aa-517fb859e280', 'idpDisplayName': 'ASTRA-OKTA-JITYPZSBjit-idp',
         'idpDomain': 'perf38.com', 'totalUsers': 0},
        {'idpId': 'cd808d9c-1a6c-4b5a-ac96-4ff93c988200', 'idpDisplayName': 'ASTRA-OKTA-JITYY96Vjit-idp',
         'idpDomain': 'perf67.com', 'totalUsers': 0},
        {'idpId': '6ab0277c-56f0-41c1-9ffe-f2b0b45dadd2', 'idpDisplayName': 'ASTRA-OKTA-JITYTKAYjit-idp',
         'idpDomain': 'perf385.com', 'totalUsers': 0},
        {'idpId': '9b975bad-6b31-4fbd-b7dd-f8161a69fc7c', 'idpDisplayName': 'ASTRA-OKTA-JITPN1GJjit-idp',
         'idpDomain': 'perf456.com', 'totalUsers': 0},
        {'idpId': 'f6142ec7-97ba-4658-8037-dab87163bb95', 'idpDisplayName': 'ASTRA-OKTA-JITL8H4Yjit-idp',
         'idpDomain': 'perf20.com', 'totalUsers': 0},
        {'idpId': '03f398a7-c691-4577-9f28-f7693962bc52', 'idpDisplayName': 'ASTRA-OKTA-JITU83JQjit-idp',
         'idpDomain': 'perf391.com', 'totalUsers': 0},
        {'idpId': '9f3b97cd-35f2-4959-b1a7-5ceca0176fb2', 'idpDisplayName': 'ASTRA-OKTA-JITJAKK5jit-idp',
         'idpDomain': 'perf176.com', 'totalUsers': 0},
        {'idpId': 'e8bfc1c0-eb4d-4552-9083-7f12a95441f2', 'idpDisplayName': 'ASTRA-OKTA-JITX8HGAjit-idp',
         'idpDomain': 'perf402.com', 'totalUsers': 0},
        {'idpId': '18789871-8d49-481e-be3b-83921c60bbda', 'idpDisplayName': 'ASTRA-OKTA-JITXT151jit-idp',
         'idpDomain': 'perf455.com', 'totalUsers': 0},
        {'idpId': '85cf1e8c-6696-4fe1-97d7-7726b9d0b176', 'idpDisplayName': 'ASTRA-OKTA-JITL06VCjit-idp',
         'idpDomain': 'perf496.com', 'totalUsers': 0},
        {'idpId': 'baad0777-ff28-4549-b9af-6a7558ef8950', 'idpDisplayName': 'ASTRA-OKTA-JITS9PCWjit-idp',
         'idpDomain': 'perf195.com', 'totalUsers': 0},
        {'idpId': '8e34fcbf-13c7-46f3-97cd-a1581b9e6693', 'idpDisplayName': 'ASTRA-OKTA-JITFZTX3jit-idp',
         'idpDomain': 'perf222.com', 'totalUsers': 0}]
    for idx, idp_tenant in enumerate(idp_tenants_with_no_users):
        mylog.info(f"processing idp no. {idx} and idp_tenants={idp_tenant.get('idpId')}")
        IDP_TENANT_DELETE_ENDPOINT = IDP_TENANT_DELETE.format(idp_registrations_id=idp_tenant.get('idpId'))
        idp_tenant_delete_resp = cclient.make_call("DELETE", IDP_TENANT_DELETE_ENDPOINT)
        mylog.debug("idp_tenant_delete response={}".format(idp_tenant_delete_resp))

    mylog.info("Test ended")
