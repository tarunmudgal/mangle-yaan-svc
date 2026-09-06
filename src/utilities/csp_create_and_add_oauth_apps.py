import concurrent.futures
import csv
import datetime
import inspect
import logging.handlers
import os
import sys
import time
import uuid
from builtins import getattr

import pkce
import requests
import urllib3
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout, SSLError, Timeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError, InsecureRequestWarning

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# define constants #
HTTP_RETRIABLE_ERRORS = (
    ConnectionError,
    ConnectTimeout,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    Timeout,
)

CODE_VERIFIER_CONST = pkce.generate_code_verifier(length=43)
CODE_CHALLENGE_CONST = pkce.get_code_challenge(CODE_VERIFIER_CONST)
REQUEST_SESSION = requests.session()
PO_AUTH_TOKEN = "ZcMhmvffR70Auq1_z4RNKTWST6tcM88CspTnxwBv4Fx1YN7rNSweha2OHGOMOpzO"
CSP_URL = "https://console-preview.cloud.company.com"
INPUT_API_TOKENS_FILE = "oauth_apps.csv"
OUTPUT_API_TOKEN_FILE = "oauth_apps_updated.csv"
MAX_WORKERS = 60

# initialize logger #
CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOGFILE_PATH = (CURRENT_DIR + os.path.sep + "{}.log".format(os.path.splitext(os.path.split(__file__)[1])[0]))
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(funcName)s] [pid=%(process)d] [%(lineno)d]: %(message)s"
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"

# initialize logger
mylog = logging.getLogger("mylogger")
mylog.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOGFILE_PATH)

console_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
formatter.converter = time.gmtime  # log UTC timestamps
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
console_handler.flush = sys.stdout.flush

mylog.addHandler(console_handler)
mylog.addHandler(file_handler)


# class to execute CSP API calls #
class CSPAPIFlows(object):
    def __init__(self, csp_url="https://console-preview.cloud.company.com", api_token=""):
        self.api_token = api_token
        self.access_token = ""
        self.session = requests.session()
        self.timeout = 60
        self.csp_url = csp_url
        self.base_url = csp_url + "/csp/gateway"
        self.update_access_token()

    def rest_request(
            self,
            method: str,
            csp_api_url: str,
            retry_count: int = 1,
            retry_sleep: int = 5,
            **kwargs: str,
    ) -> requests.Response:
        """thin wrapper over requests. Request API with retry logic implemented
        Args:
          method: request verb e.g. GET, POST, PUT, DELETE etc.
          csp_api_url: complete csp url including api resource
          retry_count: maximum number of retries allowed
          retry_sleep: sleep (in seconds) in between retries

        Returns:
          requests.Response
        """

        if retry_count < 0:
            retry_count = 0

        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout

        attempt = 0
        while attempt < retry_count + 1:
            try:
                attempt += 1
                # mylog.debug(
                #     "Sending a request with method=%s, url=%s", method, csp_api_url,
                # )
                response = getattr(self.session, method.lower())(csp_api_url, **kwargs)
                # mylog.debug(
                #     "Request with method=%s, url=%s succeeded in (%d) attempt(s)",
                #     method,
                #     csp_api_url,
                #     attempt,
                # )
                return response
            except HTTP_RETRIABLE_ERRORS as fault:
                mylog.debug(
                    "Failed to send request due to connection error. method=%s, url=%s, error=%s",
                    method,
                    csp_api_url,
                    fault,
                )
                if attempt < retry_count + 1:
                    mylog.debug("retry(%d) after %d seconds", attempt, retry_sleep)
                    time.sleep(retry_sleep)
                else:
                    mylog.exception(fault)
                    raise
            except Exception as fault:
                mylog.debug("Exception occurred in method=%s, url=%s", method, csp_api_url)
                mylog.exception(fault)
                raise

    def update_access_token(self):
        access_token_url = self.base_url + "/am/api/auth/api-tokens/authorize"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "visid_incap_1729671=8nN6ObgUQO2DZgaqE39n1MjxK18AAAAAQUIPAAAAAAAB8r3FWv5IQSDtqQiSFWMy; "
                      "nlbi_1729671=GGBSOJWSxhwQTi/AcPvC0AAAAAAMzj+SD4kv+gKLfKspMsW7; "
                      "incap_ses_1135_1729671=cVzfZWfL9GDzPfgmnVTAD5owYl8AAAAAPnB6wFOkTMNOoJ/uPACH4g==; "
                      "incap_ses_711_1729671=Iw6xVjF0ohoa4Zw/3PrdCRt1aF8AAAAADpUs5iu2LEcjkWuXCzxFuA==; "
                      "incap_ses_1132_1729671=ZHs4bdSuDATLlV6OI6y1D0/6aF8AAAAAsQh8diZEML1Ro1a0bL1fvA==",
        }
        payload = "refresh_token={}".format(self.api_token)

        mylog.debug("fetching access_token for CSP API calls")
        # response = requests.request("POST", access_token_url, headers=headers, data=payload)
        response = self.rest_request(
            "POST", access_token_url, retry_count=1, retry_sleep=5, headers=headers, data=payload,
        )

        if response.status_code == requests.codes.ok:
            self.access_token = response.json().get("access_token")
        else:
            raise Exception(
                "could not fetch access_token using Request(url={}, headers={}, payload={}). Response(status={}, "
                "text={})".format(
                    access_token_url, headers, payload, response.status_code, response.text,
                )
            )

    def make_call(
            self, verb: str, api_resource: str, expected_status_code=200, **kwargs: str
    ) -> Response:
        """
        makes an HTTP call using RESTClient. Request API Args: expected_status_code: verb: request verb e.g. GET,
        POST, PUT, DELETE etc. api_resource: api resource handle kwargs: kwargs that are supported by
        requests.request. In addition, retry_count and retry_sleep are also supported Returns: CSPResponse obj
        """
        csp_api_url = self.base_url + api_resource
        headers = {"csp-auth-token": self.access_token, "Content-Type": "application/json"}
        req_resp = self.rest_request(verb, csp_api_url, headers=headers, **kwargs)
        if req_resp.status_code == 401:
            mylog.error("Authorization error occurred for CSP API call. Updating access_token")
            self.update_access_token()
            req_resp = self.rest_request(verb, csp_api_url, headers=headers, **kwargs)

        if req_resp.status_code != expected_status_code:
            mylog.error(
                f"Error occurred while calling '{verb} {csp_api_url}'. Response status_code="
                f"{req_resp.status_code}, response_text={req_resp.text}, Request headers={headers}, "
                f"kwargs={kwargs}"
            )

        return req_resp

    def create_oauth_app(self, instance_id):
        create_oauth_app_url = f"/am/api/orgs/649cc1dc-f4be-44df-90fa-1e2331acf2e5/oauth-apps"
        create_oauth_app_payload = {
            "accessTokenTTL": 1800,
            "allowedScopes": {
                "allRoles": False,
                "generalScopes": [],
                "organizationScopes": {
                    "allRoles": False,
                    "roles": [
                        {
                            "name": "org_member"
                        },
                        {
                            "name": "org_owner"
                        },
                        {
                            "name": "service_owner"
                        }
                    ]
                },
                "servicesScopes": [
                    {
                        "serviceDefinitionId": "e42a9d48-d88b-4c3a-907e-d6c67e178bd3",
                        "allRoles": False,
                        "roles": [
                            {
                                "name": "vmc:user"
                            },
                            {
                                "name": "vmc:admin"
                            },
                            {
                                "name": "vmc:enabler"
                            },
                            {
                                "name": "vmc:service-owner"
                            },
                            {
                                "name": "vmc:member"
                            },
                            {
                                "resource": "instance:" + instance_id,
                                "name": "vmc:admin"
                            },
                            {
                                "resource": "instance:" + instance_id,
                                "name": "vmc:enabler"
                            },
                            {
                                "resource": "instance:" + instance_id,
                                "name": "vmc:member"
                            },
                            {
                                "resource": "instance:" + instance_id,
                                "name": "vmc:service-owner"
                            }
                        ]
                    }
                ]
            },
            "maxCharactersInAccessToken": 9000,
            "displayName": "App_" + str(uuid.uuid4()),
            "description": "Test_App",
            "publicClient": False,
            "grantTypes": [
                "client_credentials"
            ],
            "redirectUris": []
        }
        create_oauth_app_response = self.make_call("POST", create_oauth_app_url, json=create_oauth_app_payload)
        client_id = create_oauth_app_response.json().get("clientId")
        return client_id

    def add_oauth_app(self, default_org_id_expected, instance_id, client_id):
        add_oauth_app_url = f"/am/api/orgs/{default_org_id_expected}/clients"
        add_oauth_app_payload = {
            "organizationRoles": [
                {
                    "name": "org_member"
                },
                {
                    "name": "org_owner"
                }
            ],
            "serviceRoles": [
                {
                    "serviceDefinitionId": "e42a9d48-d88b-4c3a-907e-d6c67e178bd3",
                    "serviceRoles": [
                        {
                            "name": "vmc:user"
                        }
                    ]
                }
            ],
            "ids": [
                client_id
            ]
        }
        self.make_call("POST", add_oauth_app_url, json=add_oauth_app_payload)

    def regenerate_secret(self, client_id):
        regenerate_secret_url = f"/am/api/orgs/649cc1dc-f4be-44df-90fa-1e2331acf2e5/oauth-apps/{client_id}/secret"
        regenerate_secret_response = self.make_call("PUT", regenerate_secret_url)
        client_secret = regenerate_secret_response.json().get("clientSecret")
        return client_secret

    def remove_oauth_app_from_org(self, default_org_id_expected, client_id):
        remove_oauth_app_url = f"/am/api/orgs/{default_org_id_expected}/clients"
        remove_oauth_app_payload = {
            "ids": [
                client_id
            ]
        }
        self.make_call("DELETE", remove_oauth_app_url, json=remove_oauth_app_payload)

    def add_client_role(self, default_org_id_expected, instance_id, client_id):
        update_client_role_url = f"/am/api/clients/{client_id}/orgs/{default_org_id_expected}/roles"
        update_client_role_payload = {
            "serviceRoles": [
                {
                    "rolesToAdd": [
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:admin"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:member"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:enabler"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:service-owner"
                        }
                    ],
                    "serviceDefinitionId": "e42a9d48-d88b-4c3a-907e-d6c67e178bd3"
                }
            ]
        }
        self.make_call("PATCH", update_client_role_url, json=update_client_role_payload)

    def delete_client_role(self, default_org_id_expected, instance_id, client_id):
        update_client_role_url = f"/am/api/clients/{client_id}/orgs/{default_org_id_expected}/roles"
        update_client_role_payload = {
            "serviceRoles": [
                {
                    "rolesToRemove": [
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:admin"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:member"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:enabler"
                        },
                        {
                            "resource": "instance:" + instance_id,
                            "name": "vmc:service-owner"
                        }
                    ],
                    "serviceDefinitionId": "e42a9d48-d88b-4c3a-907e-d6c67e178bd3"
                }
            ]
        }
        self.make_call("PATCH", update_client_role_url, json=update_client_role_payload)


def process_user_information(api_flow, user_row):
    try:
        global REQUEST_SESSION
        REQUEST_SESSION = requests.session()
        mylog.debug("Processing")
        # api_flow.remove_oauth_app_from_org(user_row.get("orgId"), user_row.get("clientId"))
        clientId = api_flow.create_oauth_app(user_row.get("serviceInstance"))
        user_row["clientId"] = clientId
        api_flow.add_oauth_app(user_row.get("orgId"), user_row.get("serviceInstance"), user_row.get("clientId"))
        clientSecret = api_flow.regenerate_secret(user_row.get("clientId"))
        user_row["clientSecret"] = clientSecret
        user_row["status"] = "PASS"
    except Exception as e:
        user_row["status"] = "FAIL"
        mylog.debug("Processing Ended")
        raise
    return user_row


# main block #
def main():
    if not PO_AUTH_TOKEN:
        mylog.error("PO_AUTH_TOKEN needs to be supplied. Global vars are defined at the top")
        sys.exit()

    api_flow = CSPAPIFlows(csp_url=CSP_URL, api_token=PO_AUTH_TOKEN)

    mylog.info("Script start time: {}".format(datetime.datetime.now(datetime.timezone.utc)))
    with open(INPUT_API_TOKENS_FILE) as api_token_reader:
        csv_reader = csv.DictReader(api_token_reader)
        with open(OUTPUT_API_TOKEN_FILE, "w", newline="\n") as api_token_writer:
            csv_writer = csv.DictWriter(api_token_writer, fieldnames=csv_reader.fieldnames)
            csv_writer.writeheader()

            # in-parallel execution
            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
                execution_result = (
                    executor.submit(process_user_information, api_flow, user_row)
                    for user_row in csv_reader
                )
                for future in concurrent.futures.as_completed(execution_result):
                    try:
                        csv_writer.writerow(future.result())
                    except Exception as fault:
                        mylog.exception(fault)

            # code to debug any issue in process_user_information call. To debug, above 'in-parallel execution' block
            # can be commented and below section should be uncommented.
            # for user_row in csv_reader:
            #    process_user_information(api_flow, user_row)

    mylog.info("Script end time: {}".format(datetime.datetime.now(datetime.timezone.utc)))


if __name__ == "__main__":
    main()