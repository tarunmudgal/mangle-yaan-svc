import concurrent.futures
import csv
import datetime
import inspect
import logging.handlers
import os
import sys
import time
import uuid
import random
import string
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
PO_AUTH_TOKEN = ""
CSP_URL = "https://console-preview.cloud.vmware.com"
INPUT_API_TOKENS_FILE = "preview_300x_users.csv"
OUTPUT_API_TOKEN_FILE = "preview_300x_users_updated.csv"
MAX_WORKERS = 10
service_tickers = []

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


def create_service_ticker():
    # choose from all lowercase letter
    length = random.randrange(2, 6)
    letters = string.ascii_lowercase
    service_ticker = ''.join(random.choice(letters) for i in range(length))
    while service_tickers.count(service_ticker) != 0:
        length = random.randrange(2, 6)
        result_str = ''.join(random.choice(letters) for i in range(length))
    service_tickers.append(service_ticker)
    return service_ticker

# class to execute CSP API calls #
class CSPAPIFlows(object):
    def __init__(self, csp_url="https://console-preview.cloud.vmware.com", api_token=""):
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

    def organization_group(self, default_org_id_expected):
        mylog.debug("Processing Started for Group")
        orgs_group = f"/am/api/orgs/{default_org_id_expected}/groups"
        resp_orgs_group = self.make_call("GET", orgs_group, expected_status_code=200)
        if resp_orgs_group.json().get("totalResults") != 0:
            group_id = resp_orgs_group.json().get("results")[0].get("id")
            mylog.debug("group_id={}".format(group_id))
        else:
            payload = {"description": "Custom User Group", "name": "Custom User"}
            resp_group = self.make_call("POST", orgs_group, expected_status_code=200, json=payload)
            group_id = resp_group.json().get("id")
            mylog.debug("group_id={}".format(group_id))

        return group_id

    def new_organization_group(self, default_org_id_expected):
        mylog.debug("Processing Started for Group")
        orgs_group = f"/am/api/orgs/{default_org_id_expected}/groups"
        payload = {"description": "Custom User Group" + str(uuid.uuid4()), "name": "Custom User" + str(uuid.uuid4())}
        resp_group = self.make_call("POST", orgs_group, expected_status_code=200, json=payload)
        mylog.debug("Processing End for Group")

    def organization_group_role(self, default_org_id_expected, group_id):
        mylog.debug("Processing Started for Group Role")
        orgs_group_role = f"/am/api/orgs/{default_org_id_expected}/groups/{group_id}/roles"
        payload = {
            "organizationRoles": {
                "rolesToAdd": [
                    {
                        "name": "developer"
                    }
                ]
            },
            "notifyUsersInGroups": False
        }
        resp_group = self.make_call("PATCH", orgs_group_role, expected_status_code=200, json=payload)
        mylog.debug("Processing Done for Group Role")

    def organization_services(self, default_org_id_expected):
        mylog.debug("Processing Started for services")
        orgs_services = f"/slc/api/v2/orgs/{default_org_id_expected}/services"
        resp_orgs_services = self.make_call("GET", orgs_services, expected_status_code=200)
        if resp_orgs_services.json().get("totalResults") != 0:
            services = resp_orgs_services.json().get("results")[0].get("services")[0]
            service_url = services.get("documentSelfLink")
            service_id = service_url.split("/")[-1]
            mylog.debug("service_id={}".format(service_id))
        else:
            new_service_creation = f"/slc/api/definitions"
            payload = {
                "name": "CSP-Test-Service-Child_" + str(uuid.uuid4()),
                "display-name": "CSP-Test-Service-Child_" + str(uuid.uuid4()),
                "isDisabled": False,
                "desc-long": "This service used for testing in Dev",
                "gated": True,
                "service-roles": [
                    {
                        "type": "CUSTOMER",
                        "name": "srv_name:user",
                        "display-name": "admin user",
                        "default": True,
                        "hidden": False
                    }
                ],
                "visible": True,
                "product-identifier": "VMC-AWS",
                "supported-billing-engines": [
                    {
                        "name": "SAP",
                        "default": True
                    }
                ],
                "service-type": "FREE",
                "sellers": [
                    {
                        "enabled": True,
                        "seller": "VMWARE"
                    }
                ],
                "service-urls": {
                    "service-home": "www.cloud.vmware.com"
                },
                "serviceTicker": create_service_ticker(),
                "org-id": default_org_id_expected
            }
            resp_services = self.make_call("POST", new_service_creation, expected_status_code=201, json=payload)
            services = resp_services.json().get("refLink")
            service_id = services.split("/")[-1]
            mylog.debug("new_service_id={}".format(service_id))

            grant_service_access = f"/slc/api/service-access"
            payload = {
                "orgId": default_org_id_expected,
                "serviceDefinitionId": service_id,
                "isTosPreSigned": True
            }
            resp_grant_access = self.make_call("POST", grant_service_access, expected_status_code=202, json=payload)

        return service_id

    def new_organization_services(self, default_org_id_expected):
        mylog.debug("Processing Started for services")
        new_service_creation = f"/slc/api/definitions"
        payload = {
            "name": "CSP-Astra-Test-Service_" + str(uuid.uuid4()),
            "display-name": "CSP-Astra-Test-Service_" + str(uuid.uuid4()),
            "isDisabled": False,
            "desc-long": "This service used for testing in Preview.",
            "gated": True,
            "service-roles": [
                {
                    "type": "CUSTOMER",
                    "name": "srv_name:user",
                    "display-name": "user",
                    "default": True,
                    "hidden": False
                },
                {
                    "type": "CUSTOMER",
                    "name": "srv_name:admin",
                    "display-name": "admin",
                    "default": True,
                    "hidden": False
                }
            ],
            "visible": True,
            "product-identifier": "VMC-AWS",
            "supported-billing-engines": [
                {
                    "name": "SAP",
                    "default": True
                }
            ],
            "service-type": "FREE",
            "sellers": [
                {
                    "enabled": True,
                    "seller": "VMWARE"
                }
            ],
            "service-urls": {
                "service-home": "www.cloud.vmware.com"
            },
            "serviceTicker": create_service_ticker(),
            "org-id": default_org_id_expected
        }
        resp_services = self.make_call("POST", new_service_creation, expected_status_code=201, json=payload)
        services = resp_services.json().get("refLink")
        service_id = services.split("/")[-1]
        mylog.debug("new_service_id={}".format(service_id))

        grant_service_access = f"/slc/api/service-access"
        payload = {
            "orgId": default_org_id_expected,
            "serviceDefinitionId": service_id,
            "isTosPreSigned": True
        }
        resp_grant_access = self.make_call("POST", grant_service_access, expected_status_code=202, json=payload)
        mylog.debug("Processing End for services")

        return service_id

    def organization_oauth_app(self, default_org_id_expected):
        mylog.debug("Processing Started for oauth_app")
        orgs_oauth_apps = f"/am/api/orgs/{default_org_id_expected}/oauth-apps"
        resp_orgs_oauth_apps = self.make_call("GET", orgs_oauth_apps, expected_status_code=200)
        if resp_orgs_oauth_apps.json().get("totalResults") != 0:
            oauth_apps_id = resp_orgs_oauth_apps.json().get("results")[0].get("id")
            mylog.debug("oauth_apps_id={}".format(oauth_apps_id))
        else:
            payload = {
                "accessTokenTTL": 18000,
                "allowedScopes": {
                    "allRoles": False,
                    "generalScopes": [],
                    "organizationScopes": {
                        "allRoles": False,
                        "roles": [
                            {
                                "name": "org_owner"
                            }
                        ]
                    }
                },
                "displayName": "test_oauth_app",
                "description": "test_oauth_app",
                "publicClient": False,
                "grantTypes": [
                    "client_credentials"
                ],
                "redirectUris": []
            }
            resp_group = self.make_call("POST", orgs_oauth_apps, expected_status_code=200, json=payload)
            oauth_apps_id = resp_group.json().get("clientId")
            mylog.debug("oauth_apps_id={}".format(oauth_apps_id))

        return oauth_apps_id

    def new_organization_oauth_app(self, default_org_id_expected):
        mylog.debug("Processing Started for oauth_app")
        orgs_oauth_apps = f"/am/api/orgs/{default_org_id_expected}/oauth-apps"
        payload = {
            "accessTokenTTL": 18000,
            "allowedScopes": {
                "allRoles": False,
                "generalScopes": [],
                "organizationScopes": {
                    "allRoles": False,
                    "roles": [
                        {
                            "name": "org_owner"
                        }
                    ]
                }
            },
            "displayName": "test_oauth_app",
            "description": "test_oauth_app",
            "publicClient": False,
            "grantTypes": [
                "client_credentials"
            ],
            "redirectUris": []
        }
        resp_group = self.make_call("POST", orgs_oauth_apps, expected_status_code=200, json=payload)
        mylog.debug("Processing End for oauth_app")

    def add_user_organization(self, email):
        mylog.debug("Processing Started for user_addition")
        user_addition = f"/am/api/orgs/55e921ca-8131-4c95-a90f-647f5db4953f/invitations"
        payload = {
            "organizationRoles": [
                {
                    "name": "org_owner"
                }
            ],
            "usernames": [
                email
            ]
        }
        resp_orgs_user_details = self.make_call("POST", user_addition, expected_status_code=202, json=payload)
        mylog.debug("Processing Done for user_addition")

    def patch_organization_roles(self, default_org_id_expected):
        # Update Organization roles
        patch_org_roles = f"/am/api/orgs/{default_org_id_expected}/roles"
        org_roles_payload = {
            "roleNamesToAdd": [
                "service_owner",
                "feature_flag_manager"
            ]
        }
        resp_patch_org_roles = self.make_call("PATCH", patch_org_roles, json=org_roles_payload)

    def add_user_roles(self, default_org_id_expected, email):
        # Update Organization roles
        patch_user_roles = f"/am/api/users/{email}/orgs/{default_org_id_expected}/roles"
        user_roles_payload = {
            "rolesToAdd": [
                {
                    "name": "service_owner"
                }
            ]
        }
        resp_patch_org_roles = self.make_call("PATCH", patch_user_roles, json=user_roles_payload)

    def get_service_onboarded_in_orgs(self, default_org_id_expected):
        # Service Onboarded in Org
        get_service = f"/slc/api/definitions?orgLink=/csp/gateway/am/api/orgs/{default_org_id_expected}"
        resp_get_service = self.make_call("GET", get_service)
        if resp_get_service.json().get("totalResults") != 0:
            services_url = resp_get_service.json().get("serviceDefinitionLinks")[0]
            service_id = services_url.split("/")[-1]
            mylog.debug("service_id={}".format(service_id))
        else:
            new_service_creation = f"/slc/api/definitions"
            payload = {
                "name": "CSP-Astra-Test-Service_" + str(uuid.uuid4()),
                "display-name": "CSP-Astra-Test-Service_" + str(uuid.uuid4()),
                "isDisabled": False,
                "desc-long": "This service used for testing in Preview",
                "gated": True,
                "service-roles": [
                    {
                        "type": "CUSTOMER",
                        "name": "srv_name:user",
                        "display-name": "admin user",
                        "default": True,
                        "hidden": False
                    }
                ],
                "visible": True,
                "product-identifier": "VMC-AWS",
                "supported-billing-engines": [
                    {
                        "name": "SAP",
                        "default": True
                    }
                ],
                "service-type": "FREE",
                "sellers": [
                    {
                        "enabled": True,
                        "seller": "VMWARE"
                    }
                ],
                "service-urls": {
                    "service-home": "www.cloud.vmware.com"
                },
                "serviceTicker": create_service_ticker(),
                "org-id": default_org_id_expected
            }
            resp_services = self.make_call("POST", new_service_creation, expected_status_code=201, json=payload)
            services = resp_services.json().get("refLink")
            service_id = services.split("/")[-1]
            mylog.debug("new_service_id={}".format(service_id))

            grant_service_access = f"/slc/api/service-access"
            payload = {
                "orgId": default_org_id_expected,
                "serviceDefinitionId": service_id,
                "isTosPreSigned": True
            }
            resp_grant_access = self.make_call("POST", grant_service_access, expected_status_code=202, json=payload)

        return service_id

    def get_service_onboarded_in_orgs1(self, default_org_id_expected):
        # Service Onboarded in Org
        get_service = f"/slc/api/definitions?orgLink=/csp/gateway/am/api/orgs/{default_org_id_expected}"
        resp_get_service = self.make_call("GET", get_service)
        services_url = resp_get_service.json().get("serviceDefinitionLinks")[0]
        service_id = services_url.split("/")[-1]
        mylog.debug("service_id={}".format(service_id))

        return service_id

    def check_refresh_token(self, refresh_token):
        mylog.debug("Processing Started for token validation")
        check = f"/am/api/auth/api-tokens/authorize?refresh_token={refresh_token}"
        resp_orgs_user_details = self.make_call("POST", check, expected_status_code=200)
        status = resp_orgs_user_details.status_code
        if status != 200:
            status = "FAIL"
        else:
            status = "PASS"
        mylog.debug("Processing Done for token validation")

        return status

    def update_service_definition_with_service_ticker(self, service_id):
        # Update Organization roles
        patch_service_definition = f"/slc/api/definitions/external/{service_id}"
        patch_service_definition_payload = {
            "serviceTicker": create_service_ticker()
        }
        self.make_call("PATCH", patch_service_definition, json=patch_service_definition_payload)

    def remove_service_from_org(self, service_id):
        deny_service_access = f"/slc/api/definitions/external/{service_id}/org-access/actions?action=DENY_ACCESS"
        deny_service_access_payload = {
            "orgId": "19a053ad-9cc3-4aa3-831c-5d3fe2ca0a28"
        }
        self.make_call("POST", deny_service_access, json=deny_service_access_payload)

        delete_service_access = f"/slc/api/service-access"
        delete_service_access_payload = {
            "serviceDefinitionId": {service_id},
            "orgId": "19a053ad-9cc3-4aa3-831c-5d3fe2ca0a28"
        }
        self.make_call("DELETE", delete_service_access, json=delete_service_access_payload)

    def get_instance_count(self, service_id):
        get_instance = f"/slc/api/definitions/external/{service_id}/service-instances"
        instance_response = self.make_call("GET", get_instance)
        count = instance_response.json().get("totalResults")
        return count

    def get_oauth_app_count(self, default_org_id_expected):
        get_oauth_app = f"/am/api/orgs/{default_org_id_expected}/oauth-apps"
        get_oauth_app_response = self.make_call("GET", get_oauth_app)
        count = get_oauth_app_response.json().get("totalResults")
        return count


def process_user_information(api_flow, user_row):
    try:
        global REQUEST_SESSION
        REQUEST_SESSION = requests.session()
        mylog.debug("processing user={}".format(user_row))
        # groupId = api_flow.organization_group(user_row.get("orgId"))
        # user_row["groupId"] = groupId
        # api_flow.organization_group_role(user_row.get("orgId"), user_row.get("groupId"))
        # serviceId = api_flow.organization_services(user_row.get("orgId"))
        # user_row["ServiceDefinitionId"] = serviceId
        # clientId = api_flow.organization_oauth_app(user_row.get("orgId"))
        # user_row["clientId"] = clientId
        # user_row["status"] = "PASS"
        # mylog.debug("processing done for user={}".format(user_row.get("user")))
        # mylog.debug("processing org={}".format(user_row.get("user")))
        # api_flow.add_user_organization(user_row.get("user"))
        # mylog.debug("processing done for org={}".format(user_row.get("user")))
        # status = api_flow.check_refresh_token(user_row.get("refreshToken"))
        # user_row["status"] = status
        # api_flow.new_organization_group(user_row.get("orgId"))
        # service_id = api_flow.new_organization_services(user_row.get("orgId"))
        # user_row["ServiceDefinitionId"] = service_id
        # api_flow.new_organization_oauth_app(user_row.get("orgId"))
        # api_flow.add_user_roles(user_row.get("orgId"), user_row.get("user"))
        service_id = api_flow.get_service_onboarded_in_orgs1(user_row.get("orgId"))
        user_row["ServiceDefinitionId"] = service_id
        # api_flow.update_service_definition_with_service_ticker(user_row.get("ServiceDefinitionId"))
        # api_flow.remove_service_from_org(user_row.get("ServiceDefinitionId"))
        user_row["status"] = "PASS"
        # count = api_flow.get_instance_count(user_row.get("ServiceDefinitionId"))
        # count = api_flow.get_oauth_app_count(user_row.get("org_id"))
        # user_row["count"] = count
    except Exception as e:
        user_row["status"] = "FAIL"
        mylog.debug("processing failed for user={}".format(user_row.get("orgId")))
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
