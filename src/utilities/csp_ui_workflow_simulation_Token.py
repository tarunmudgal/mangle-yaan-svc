import concurrent.futures
import csv
import datetime
import inspect
import logging.handlers
import os
import re
import sys
import time
import urllib.parse as urlparse
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
    ConnectTimeoutError,
    ReadTimeout,
    SSLError,
    Timeout,
)

CODE_VERIFIER_CONST = pkce.generate_code_verifier(length=43)
CODE_CHALLENGE_CONST = pkce.get_code_challenge(CODE_VERIFIER_CONST)
REQUEST_SESSION = requests.session()
PO_AUTH_TOKEN = "8Bj3wiATU_3gg1Bm2OBDdOIW2IxwB0rWR9RHdYqWIQR5VsOiWir702h4wHIb2Wm7"
CSP_URL = "https://console-preview.cloud.vmware.com"
INPUT_API_TOKENS_FILE = "preview_300x_users.csv"
OUTPUT_API_TOKEN_FILE = "preview_300x_users_updated.csv"
MAX_WORKERS = 60

# initialize logger #
CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOGFILE_PATH = (
    CURRENT_DIR + os.path.sep + "{}.log".format(os.path.splitext(os.path.split(__file__)[1])[0])
)
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
        """thin wrapper over requests.request API with retry logic implemented
        Args:
          method: request verb e.g. GET, POST, PUT, DELETE etc.
          csp_api_url: complete csp url including api resource
          retry_count: maxium number of retries allowed
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
            "Cookie": "visid_incap_1729671=8nN6ObgUQO2DZgaqE39n1MjxK18AAAAAQUIPAAAAAAAB8r3FWv5IQSDtqQiSFWMy; nlbi_1729671=GGBSOJWSxhwQTi/AcPvC0AAAAAAMzj+SD4kv+gKLfKspMsW7; incap_ses_1135_1729671=cVzfZWfL9GDzPfgmnVTAD5owYl8AAAAAPnB6wFOkTMNOoJ/uPACH4g==; incap_ses_711_1729671=Iw6xVjF0ohoa4Zw/3PrdCRt1aF8AAAAADpUs5iu2LEcjkWuXCzxFuA==; incap_ses_1132_1729671=ZHs4bdSuDATLlV6OI6y1D0/6aF8AAAAAsQh8diZEML1Ro1a0bL1fvA==",
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
                "could not fetch access_token using Request(url={}, headers={}, payload={}). Response(status={}, text={})".format(
                    access_token_url, headers, payload, response.status_code, response.text,
                )
            )

    def make_call(
        self, verb: str, api_resource: str, expected_status_code=200, **kwargs: str
    ) -> Response:
        """
        makes a HTTP call using RESTClient.request API
        Args:
            verb: request verb e.g. GET, POST, PUT, DELETE etc.
            api_resource: api resource handle
            kwargs: kwargs that are supported by requests.request. In addition, retry_count and retry_sleep are also supported
        Returns:
            CSPResponse obj
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

    def perform_corrections(self, user_email, default_org_id_expected):
        default_org_resource_v1 = f"/am/api/users/{user_email}/default-org"
        resp_default_org = self.make_call("GET", default_org_resource_v1)

        # default_org_id = resp_default_org.json().get('refLink').split('/')[-1]
        if (
            resp_default_org.json().get("refLink") is None
            or resp_default_org.json().get("refLink").split("/")[-1] != default_org_id_expected
        ):
            user_orgs_res = f"/am/api/users/{user_email}/orgs"
            resp_user_orgs = self.make_call("GET", user_orgs_res)
            user_orgs = [
                org_uri.split("/")[-1] for org_uri in resp_user_orgs.json().get("refLinks")
            ]
            if default_org_id_expected not in user_orgs:
                add_user_to_org_res = f"/am/api/orgs/{default_org_id_expected}/invitations"
                payload = {"organizationRoles": [{"name": "org_owner"}], "usernames": [user_email]}
                resp_add_user_to_org = self.make_call(
                    "POST", add_user_to_org_res, expected_status_code=202, json=payload
                )

            default_org_resource_v2 = f"/am/api/v2/users/{user_email}/profile/default-org"
            default_org_payload = {"id": default_org_id_expected}
            resp_default_org = self.make_call(
                "PUT", default_org_resource_v2, json=default_org_payload
            )

        api_tokens_resource = (
            f"/am/api/users/{user_email}/orgs/{default_org_id_expected}/api-tokens"
        )
        resp_delete_api_tokens = self.make_call("DELETE", api_tokens_resource)


# class to perform CSP UI calls simulation #
class CSPUIFlows(object):
    def __init__(self):
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def execute_my_vmware_flow(self, idp_login_url, csp_url, username, password):

        ####### Request 3 GAZ HOST
        # Set Pre-Parameters:
        gazheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Referer": csp_url
            + "/csp/gateway/discovery"
            + "?state="
            + csp_url
            + "%2Fcsp%2Fgateway%2Fportal%2F"
            + "&redirect_uri="
            + csp_url
            + "%2Fcsp%2Fgateway%2Fportal%2Fauth%2Fcallback",
        }
        # Execute
        resp = REQUEST_SESSION.get(
            idp_login_url, verify=False, headers=gazheaders, allow_redirects=True
        )
        # Fetch post parameters
        csp_vidm_host = (
            urlparse.urlparse(resp.history[3].url).scheme
            + "://"
            + urlparse.urlparse(resp.history[3].url).netloc
        )
        OAMHOST = urlparse.urlparse(resp.url).scheme + "://" + urlparse.urlparse(resp.url).netloc

        mylog.debug("csp_vidm_host={}".format(csp_vidm_host))
        mylog.debug("OAMHOST={}".format(OAMHOST))

        fetchedReferer = resp.url

        ####### Request 4 UAT - OAM HOST POST CREDIT SUBMIT USER password
        oamheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Content-type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": fetchedReferer,
        }

        oam_postparams = {"username": username, "password": password}
        resp = REQUEST_SESSION.post(
            OAMHOST + "/oam/server/auth_cred_submit?Auth-AppID=SCSP",
            data=oam_postparams,
            verify=False,
            headers=oamheaders,
            allow_redirects=True,
        )
        # Fetch post parameters
        fetched_saml_relay_response_dict = self.extract_all_input_type_parameters_from_html(
            resp.text, "name"
        )

        ####### Request 5 CSP-IDM HOST - POST - SAML RESPONSE
        oamheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Content-type": "application/x-www-form-urlencoded",
        }
        resp = REQUEST_SESSION.post(
            csp_vidm_host + "/SAAS/auth/saml/response",
            data=fetched_saml_relay_response_dict,
            verify=False,
            headers=oamheaders,
            allow_redirects=True,
        )

        if resp.status_code == 400:
            raise Exception(
                "Error occurred while executing {} url. status_code={} response={}".format(
                    resp.url, resp.status_code, resp.text
                )
            )

        return resp

    def execute_local_vidm_flow(self, idp_login_url, csp_url, username, password, gaz_host):

        session = requests.Session()
        # Get IDP response
        resp = session.get(
            idp_login_url, verify=False, headers=self.headers, allow_redirects=False
        )

        # Get GAZ response
        resp = session.get(resp.next.url, verify=False, headers=self.headers, allow_redirects=True)
        jwt = re.findall('jwt" value="(.*)"', resp.text)[0]
        relay_state = re.findall('relay-state" value="(.*)"', resp.text)[0]

        # Request 4 /authcontrol/auth/request
        resp = session.post(
            "https://csp-local.vidmpreview.com/authcontrol/auth/request",
            data={"jwt": jwt, "relay-state": relay_state, "is-local-admin": False},
            verify=False,
            headers=self.headers,
            allow_redirects=True,
        )
        context_id = "CSP-LOCAL" + re.findall('value="CSP-LOCAL(.*)"', resp.text)[0]

        # Request 5 /authcontrol/authenticate
        resp = session.post(
            "https://csp-local.vidmpreview.com/authcontrol/authenticate",
            data={
                "userInput": "system",
                "username": username.split("@")[0],
                "password": password,
                "contextId": context_id,
                "domain": username.split("@")[1],
            },
            verify=False,
            headers=self.headers,
            allow_redirects=True,
        )
        jwt = re.findall('jwt" value="(.*)"', resp.text)[0]
        relay_state = re.findall('relay-state" value="(.*)"', resp.text)[0]

        # Request 6 /federation/auth/response/internal
        resp = session.post(
            "https://csp-local.vidmpreview.com/federation/auth/response/internal",
            data={"jwt": jwt, "relay-state": relay_state},
            verify=False,
            headers=self.headers,
            allow_redirects=True,
        )
        return resp

    def extract_discovery_url_from_csp_url(self, csp_url, username):
        csp_discovery_url = ""
        if "dev" in csp_url:
            csp_discovery_url = (
                "https://console-dev.cloud.vmware.com/csp/gateway/am/api/auth/discovery?"
                + "username="
                + username
                + "&"
                + "state=test.&"
                + "redirect_uri=https://console-dev.cloud.vmware.com/csp/gateway/portal&"
                + "client_id=csp_gaz_pkce_portal_client_id&"
                + "code_challenge="
                + str(CODE_CHALLENGE_CONST)
                + "&"
                + "code_challenge_method=S256"
            )
        elif "preview" in csp_url:
            csp_discovery_url = (
                "https://console-preview.cloud.vmware.com/csp/gateway/am/api/auth/discovery?"
                + "username="
                + username
                + "&"
                + "state=test.&"
                + "redirect_uri=https://console-preview.cloud.vmware.com/csp/gateway/portal&"
                + "client_id=csp_preview_pkce_portal_client_id&"
                + "code_challenge="
                + str(CODE_CHALLENGE_CONST)
                + "&"
                + "code_challenge_method=S256"
            )

        return csp_discovery_url

    def get_idp_login_url(self, csp_url, username):
        discovery_url = self.extract_discovery_url_from_csp_url(csp_url, username)

        cspheaders = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Content-type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

        resp = REQUEST_SESSION.get(discovery_url, verify=False, headers=cspheaders)
        try:
            json_data = resp.json()
        except Exception as fault:
            mylog.debug("Exception occurred while fetching idp_login_url")
            raise

        idp_login_url = json_data["idpLoginUrl"]

        mylog.debug("idp_login_url={}".format(idp_login_url))
        return idp_login_url

    def fetch_tokens(self, resp, type="access_token"):
        # Fetch tokens

        # resp = json.loads(resp.text)
        resp = resp.json()
        if type == "" or type == "access_token":
            fetchedToken = resp["access_token"]
        elif type == "refresh_token":
            fetchedToken = resp["refreshToken"]
        elif type == "id_token":
            fetchedToken = resp["idToken"]
        elif type == "all":
            fetchedToken = resp["access_token"]
            fetchedRefreshToken = resp["refreshToken"]
            fetchedIdToken = resp["idToken"]
            return {
                "access_token": str(fetchedToken),
                "refresh_token": str(fetchedRefreshToken),
                "id_token": str(fetchedIdToken),
            }
        return str(fetchedToken)

    def generate_auth_token(self, csp_url, user_email, password):
        """
        generates auth token
        """

        # Fetch IDP Login Url
        idp_login_url = self.get_idp_login_url(csp_url, user_email)

        ####### Flow paths based on username #####
        resp = None
        if "@csp.local" in user_email:
            gaz_host = (
                urlparse.urlparse(idp_login_url).scheme
                + "://"
                + urlparse.urlparse(idp_login_url).netloc
            )
            resp = self.execute_local_vidm_flow(
                idp_login_url, csp_url, user_email, password, gaz_host
            )
        else:
            resp = self.execute_my_vmware_flow(idp_login_url, csp_url, user_email, password)
            mylog.debug("execute_my_vmware_flow resp.url={}".format(resp.url))

        if csp_url in resp.url:
            code = self.extract_token_from_url(resp.url, "code")[0]
            authorize_uri = "/csp/gateway/am/api/auth/authorize"

            csp_authorize_uri = ""
            authrization_str = ""
            if "dev" in csp_url:
                csp_authorize_uri = (
                    csp_url
                    + authorize_uri
                    + "?grant_type=authorization_code&"
                    + "client_id=csp_gaz_pkce_portal_client_id&"
                    + "redirect_uri=https%3A%2F%2Fconsole-dev.cloud.vmware.com%2Fcsp%2Fgateway%2Fportal&"
                    + "code="
                    + str(code)
                    + "&"
                    + "code_verifier="
                    + str(CODE_VERIFIER_CONST)
                )
                authrization_str = "Basic Y3NwX2dhel9wa2NlX3BvcnRhbF9jbGllbnRfaWQ6"
            elif "preview" in csp_url:
                csp_authorize_uri = csp_url + authorize_uri + "?grant_type=authorization_code&" + "client_id=csp_gaz_pkce_portal_client_id&" + "redirect_uri=https%3A%2F%2Fconsole-preview.cloud.vmware.com%2Fcsp%2Fgateway" "%2Fportal&" + "code=" + str(
                    code
                ) + "&" + "code_verifier=" + str(
                    CODE_VERIFIER_CONST
                )
                authrization_str = "Basic Y3NwX3ByZXZpZXdfcGtjZV9wb3J0YWxfY2xpZW50X2lkOg=="

            mylog.debug("csp_authorize_uri={}".format(csp_authorize_uri))
            resp = REQUEST_SESSION.post(
                csp_authorize_uri,
                verify=False,
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "authorization": authrization_str,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
                },
            )
            return self.fetch_tokens(resp, type="access_token")
        else:
            raise Exception(
                "Something went wrong for user={}. url={} status_code={} response={}".format(
                    user_email, resp.status_code, resp.url, resp.content
                )
            )

    def create_new_api_token(self, csp_url, user_email, auth_token, default_org_id):

        loggedin_api_tokens_uri = (
            f"{csp_url}/csp/gateway/am/api/loggedin/user/orgs/{default_org_id}/api-tokens"
        )
        loggedin_api_tokens_payload = {
            "tokenName": "Test",
            "refreshTokenTTL": 2147483647,
            "allowedScopes": {
                "allRoles": False,
                "generalScopes": ["openid", "group_names", "group_ids"],
                "organizationScopes": {"roles": [{"name": "org_owner"}, {"name": "org_member"}]},
                "servicesScopes": [],
            },
        }
        resp_create_api_token = REQUEST_SESSION.post(
            loggedin_api_tokens_uri,
            json=loggedin_api_tokens_payload,
            headers={"csp-auth-token": auth_token},
        )
        if resp_create_api_token.status_code == 200:
            resp_create_api_token = resp_create_api_token.json()
        else:
            mylog.error(
                "Error occurred while creating new api token for user={}".format(user_email)
            )
        idp_login_url = resp_create_api_token.get("idpLoginUrl")
        resp_idp_login = REQUEST_SESSION.get(idp_login_url, headers={"csp-auth-token": auth_token})
        api_token = ""
        for resp_history in resp_idp_login.history:
            if "/csp/gateway/portal/#/user/tokens?success#" in resp_history.headers.get(
                "Location", ""
            ):
                api_token = resp_history.headers.get("Location", "").split("success#")[1]

        if not api_token:
            raise Exception(
                "Error occurred while fetching new api auth token for user={}".format(user_email)
            )

        return api_token

    def extract_all_input_type_parameters_from_html(self, html_data, parameter_name):
        """
        This method will extract said parameter from HTML Body
        :param html_data:'<HTML><BODY <FORM METHOD="POST"<INPUT type="hidden" NAME="RelayState"
        VALUE="a3434cfb59f61"/></FORM></BODY></HTML>
        :param parameter_name:NAME
        :returns:Dictionary of Extracted values for specified parameter
        """
        soup = BeautifulSoup(html_data, "html.parser")
        resultsdict = {}
        for name in soup.find_all("input"):
            resultsdict.update({name.get(parameter_name): name.get("value")})
        return resultsdict

    def extract_token_from_url(self, url_data, parameter_name):
        """
        This method will extract said parameter from URL Body
        :param url_data:'https://dev.csp.vmware.com/csp/gateway/portal/?token=eyJhbGci'
        :param parameter_name:token
        :return: Extracted Value of specified parameter
        """
        urldata = urlparse.urlparse(url_data)
        result = urlparse.parse_qs(urldata.query)
        value = result[parameter_name]
        return value


def process_user_information(api_flow, ui_flow, user_row):
    try:
        global REQUEST_SESSION
        REQUEST_SESSION = requests.session()
        mylog.debug("processing user={}".format(user_row))
        fetched_access_token = ui_flow.generate_auth_token(
            CSP_URL, user_row.get("user"), user_row.get("password")
        )
        # mylog.info("fetched_access_token={}".format(fetched_access_token))

        api_flow.perform_corrections(user_row.get("user"), user_row.get("orgId"))
        new_api_token = ui_flow.create_new_api_token(
            CSP_URL, user_row.get("user"), fetched_access_token, user_row.get("orgId")
        )
        mylog.info("new_api_token={}".format(new_api_token))

        user_row["refreshToken"] = new_api_token
        user_row["status"] = "PASS"
        mylog.debug("processing done for user={}".format(user_row.get("user")))
    except Exception as e:
        user_row["status"] = "FAIL"
        mylog.debug("processing failed for user={}".format(user_row.get("user")))
        raise

    return user_row


# main block #
if __name__ == "__main__":
    api_flow = CSPAPIFlows(csp_url=CSP_URL, api_token=PO_AUTH_TOKEN)
    ui_flow = CSPUIFlows()

    mylog.info("Script start time: {}".format(datetime.datetime.now(datetime.timezone.utc)))
    with open(INPUT_API_TOKENS_FILE) as api_token_reader:
        csv_reader = csv.DictReader(api_token_reader)
        with open(OUTPUT_API_TOKEN_FILE, "w", newline="\n") as api_token_writer:
            csv_writer = csv.DictWriter(api_token_writer, fieldnames=csv_reader.fieldnames)
            csv_writer.writeheader()

            # in-parallel refresh tokens generation
            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
                execution_result = (
                    executor.submit(process_user_information, api_flow, ui_flow, user_row)
                    for user_row in csv_reader
                )
                for future in concurrent.futures.as_completed(execution_result):
                    try:
                        csv_writer.writerow(future.result())
                    except Exception as fault:
                        mylog.exception(fault)

    mylog.info("Script end time: {}".format(datetime.datetime.now(datetime.timezone.utc)))
