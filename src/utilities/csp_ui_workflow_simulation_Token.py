import argparse
import inspect
import logging
import logging.handlers
import os
import re
import sys
import time
import urllib.parse as urlparse

import pkce
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import csv

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


code_verifier_const = pkce.generate_code_verifier(length=43)
code_challenge_const = pkce.get_code_challenge(code_verifier_const)
REQUEST_SESSION = requests.session()


CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOGFILE_PATH = CURRENT_DIR + os.path.sep + "{}.log".format(os.path.splitext(__file__)[0])
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"

# initialize logger
mylog = logging.getLogger("mylogger")
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


class AuthToken(object):
    def __init__(self):
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def execute_my_vmware_flow(self, idp_login_url, csp_url, username, password):

        ####### Request 3 GAZ HOST
        # Set Pre-Parameters:
        gazheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Referer": csp_url + '/csp/gateway/discovery' + '?state=' + csp_url + '%2Fcsp%2Fgateway%2Fportal%2F'
                       + '&redirect_uri=' + csp_url + '%2Fcsp%2Fgateway%2Fportal%2Fauth%2Fcallback'}
        # Execute
        resp = REQUEST_SESSION.get(idp_login_url, verify=False, headers=gazheaders, allow_redirects=True)
        # Fetch post parameters
        csp_vidm_host = urlparse.urlparse(resp.history[3].url).scheme + '://' \
                        + urlparse.urlparse(resp.history[3].url).netloc
        OAMHOST = urlparse.urlparse(resp.url).scheme + '://' + urlparse.urlparse(resp.url).netloc
        fetchedReferer = resp.url

        ####### Request 4 UAT - OAM HOST POST CREDIT SUBMIT USER password
        oamheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Content-type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest", "Referer": fetchedReferer}

        oam_postparams = {"username": username, "password": password}
        resp = REQUEST_SESSION.post(OAMHOST + '/oam/server/auth_cred_submit?Auth-AppID=SCSP', data=oam_postparams,
                                    verify=False, headers=oamheaders, allow_redirects=True)
        # Fetch post parameters
        fetched_saml_relay_response_dict = self.extract_all_input_type_parameters_from_html(resp.text, 'name')

        ####### Request 5 CSP-IDM HOST - POST - SAML RESPONSE
        oamheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Content-type": "application/x-www-form-urlencoded"}
        resp = REQUEST_SESSION.post(csp_vidm_host + '/SAAS/auth/saml/response', data=fetched_saml_relay_response_dict,
                                    verify=False, headers=oamheaders, allow_redirects=True)
        return resp

    def execute_local_vidm_flow(self, idp_login_url, csp_url, username, password, gaz_host):

        session = requests.Session()
        # Get IDP response
        resp = session.get(idp_login_url, verify=False, headers=self.headers, allow_redirects=False)

        # Get GAZ response
        resp = session.get(resp.next.url, verify=False, headers=self.headers, allow_redirects=True)
        jwt = re.findall("jwt\" value=\"(.*)\"", resp.text)[0]
        relay_state = re.findall("relay-state\" value=\"(.*)\"", resp.text)[0]

        # Request 4 /authcontrol/auth/request
        resp = session.post("https://csp-local.vidmpreview.com/authcontrol/auth/request",
                            data={'jwt': jwt, 'relay-state': relay_state, "is-local-admin": False},
                            verify=False, headers=self.headers, allow_redirects=True)
        context_id = "CSP-LOCAL" + re.findall("value=\"CSP-LOCAL(.*)\"", resp.text)[0]

        # Request 5 /authcontrol/authenticate
        resp = session.post("https://csp-local.vidmpreview.com/authcontrol/authenticate",
                            data={'userInput': "system", 'username': username.split('@')[0], "password": password,
                                  "contextId": context_id, "domain": username.split('@')[1]}, verify=False,
                            headers=self.headers, allow_redirects=True)
        jwt = re.findall("jwt\" value=\"(.*)\"", resp.text)[0]
        relay_state = re.findall("relay-state\" value=\"(.*)\"", resp.text)[0]

        # Request 6 /federation/auth/response/internal
        resp = session.post("https://csp-local.vidmpreview.com/federation/auth/response/internal",
                            data={'jwt': jwt, 'relay-state': relay_state}, verify=False,
                            headers=self.headers, allow_redirects=True)
        return resp

    def extract_discovery_url_from_csp_url(self, csp_url, username):
        csp_discovery_url = ''
        if 'dev' in csp_url:
            csp_discovery_url = 'https://console-dev.cloud.vmware.com/csp/gateway/am/api/auth/discovery?' \
                                + 'username=' + username + '&' + 'state=test.&' \
                                + 'redirect_uri=https://console-dev.cloud.vmware.com/csp/gateway/portal&' \
                                + 'client_id=csp_gaz_pkce_portal_client_id&' + 'code_challenge=' \
                                + str(code_challenge_const) + '&' + 'code_challenge_method=S256'
        elif 'preview' in csp_url:
            csp_discovery_url = 'https://console-preview.cloud.vmware.com/csp/gateway/am/api/auth/discovery?' \
                                + 'username=' + username + '&' + 'state=test.&' \
                                + 'redirect_uri=https://console-preview.cloud.vmware.com/csp/gateway/portal&' \
                                + 'client_id=csp_preview_pkce_portal_client_id&' + 'code_challenge=' \
                                + str(code_challenge_const) + '&' + 'code_challenge_method=S256'

        return csp_discovery_url

    def get_idp_login_url(self, csp_url, username):
        discovery_url = self.extract_discovery_url_from_csp_url(csp_url, username)

        cspheaders = {"Accept": "application/json, text/javascript, */*; q=0.01", "Accept-Encoding": "gzip, deflate",
                      "Content-type": "application/json", "X-Requested-With": "XMLHttpRequest"}

        resp = REQUEST_SESSION.get(discovery_url, verify=False, headers=cspheaders)
        json_data = resp.json()
        idp_login_url = json_data['idpLoginUrl']

        return idp_login_url

    def fetch_tokens(self, resp, type="access_token"):
        # Fetch tokens

        # resp = json.loads(resp.text)
        resp = resp.json()
        if (type == "" or type == "access_token"):
            fetchedToken = resp['access_token']
        elif (type == "refresh_token"):
            fetchedToken = resp['refreshToken']
        elif (type == "id_token"):
            fetchedToken = resp['idToken']
        elif (type == "all"):
            fetchedToken = resp['access_token']
            fetchedRefreshToken = resp['refreshToken']
            fetchedIdToken = resp['idToken']
            return {"access_token": str(fetchedToken),
                    "refresh_token": str(fetchedRefreshToken),
                    "id_token": str(fetchedIdToken)}
        return str(fetchedToken)

    def generate_auth_token(self, csp_url, user_email, password):
        """
        generates auth token
        """

        # Fetch IDP Login Url
        idp_login_url = self.get_idp_login_url(csp_url, user_email)

        ####### Flow paths based on username #####
        resp = None
        if '@csp.local' in user_email:
            gaz_host = urlparse.urlparse(idp_login_url).scheme + '://' + urlparse.urlparse(idp_login_url).netloc
            resp = self.execute_local_vidm_flow(idp_login_url, csp_url, user_email, password, gaz_host)
        else:
            resp = self.execute_my_vmware_flow(idp_login_url, csp_url, user_email, password)

        if (csp_url in resp.url):
            code = self.extract_token_from_url(resp.url, 'code')[0]
            authorize_uri = "/csp/gateway/am/api/auth/authorize"

            csp_authorize_uri = ''
            authrization_str = ''
            if 'dev' in csp_url:
                csp_authorize_uri = csp_url + authorize_uri + '?grant_type=authorization_code&' \
                                    + 'client_id=csp_gaz_pkce_portal_client_id&' \
                                    + 'redirect_uri=https%3A%2F%2Fconsole-dev.cloud.vmware.com%2Fcsp%2Fgateway%2Fportal&' \
                                    + 'code=' + str(code) + '&' + 'code_verifier=' + str(code_verifier_const)
                authrization_str = "Basic Y3NwX2dhel9wa2NlX3BvcnRhbF9jbGllbnRfaWQ6"
            elif 'preview' in csp_url:
                csp_authorize_uri = csp_url + authorize_uri + '?grant_type=authorization_code&' \
                                    + 'client_id=csp_gaz_pkce_portal_client_id&' \
                                    + 'redirect_uri=https%3A%2F%2Fconsole-preview.cloud.vmware.com%2Fcsp%2Fgateway' \
                                      '%2Fportal&' \
                                    + 'code=' + str(code) + '&' + 'code_verifier=' + str(code_verifier_const)
                authrization_str = "Basic Y3NwX3ByZXZpZXdfcGtjZV9wb3J0YWxfY2xpZW50X2lkOg=="
            resp = REQUEST_SESSION.post(csp_authorize_uri, verify=False,
                                        headers={"Content-type": "application/x-www-form-urlencoded",
                                                 "authorization": authrization_str})
            return self.fetch_tokens(resp, type="access_token")
        else:
            mylog.error("Something went wrong for user={}. status_code={} response={}".format(user_email,
                                                                                              resp.status_code,
                                                                                            resp.text))
            breakpoint()
            sys.exit()

    def create_new_api_token(self, csp_url, user_email, auth_token):
        default_org_uri = f"{csp_url}/csp/gateway/am/api/loggedin/user/default-org"
        resp_default_org = REQUEST_SESSION.get(default_org_uri, headers={'csp-auth-token': auth_token})
        if not resp_default_org.status_code == 200:
            mylog.error("Error occurred while fetching default org for user={}".format(user_email))
            sys.exit()

        default_org_id = resp_default_org.json().get('refLink').split('/')[-1]
        loggedin_api_tokens_uri = f"{csp_url}/csp/gateway/am/api/loggedin/user/orgs/{default_org_id}/api-tokens"
        loggedin_api_tokens_payload = {
            "tokenName": "Test",
            "refreshTokenTTL": 2147483647,
            "allowedScopes": {
                "allRoles": False,
                "generalScopes": [
                    "openid",
                    "group_names",
                    "group_ids"
                ],
                "organizationScopes": {
                    "roles": [
                        {
                            "name": "org_owner"
                        },
                        {
                            "name": "org_member"
                        }
                    ]
                },
                "servicesScopes": []
            }
        }
        resp_create_api_token = REQUEST_SESSION.post(loggedin_api_tokens_uri, json=loggedin_api_tokens_payload,
                                                     headers={'csp-auth-token': auth_token})
        if resp_create_api_token.status_code == 200:
            resp_create_api_token = resp_create_api_token.json()
        else:
            mylog.error("Error occurred while creating new api token for user={}".format(user_email))
            sys.exit()
        idp_login_url = resp_create_api_token.get("idpLoginUrl")
        resp_idp_login = REQUEST_SESSION.get(idp_login_url, headers={'csp-auth-token': auth_token})
        api_token = ''
        for resp_history in resp_idp_login.history:
            if '/csp/gateway/portal/#/user/tokens?success#' in resp_history.headers.get('Location', ''):
                api_token = resp_history.headers.get('Location', '').split('success#')[1]

        if not api_token:
            mylog.error("Error occurred while fetching new api auth token for user={}".format(user_email))
            sys.exit()

        return api_token


    def clean_all_api_tokens(self, csp_url, user_email, auth_token):
        default_org_uri = f"{csp_url}/csp/gateway/am/api/loggedin/user/default-org"
        resp_default_org = REQUEST_SESSION.get(default_org_uri, headers={'csp-auth-token': auth_token})
        if not resp_default_org.status_code == 200:
            mylog.error("Error occurred while fetching default org for user={}".format(user_email))
            sys.exit()

        default_org_id = resp_default_org.json().get('refLink').split('/')[-1]
        loggedin_api_tokens_uri = f"{csp_url}/csp/gateway/am/api/loggedin/user/orgs/{default_org_id}/api-tokens"
        resp_delete_api_tokens = REQUEST_SESSION.delete(loggedin_api_tokens_uri, headers={'csp-auth-token': auth_token})
        if resp_delete_api_tokens.status_code != 200:
            mylog.error("Error occurred while deleting api tokens for user={}".format(user_email))
            sys.exit()


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
        for name in soup.find_all('input'):
            resultsdict.update({name.get(parameter_name): name.get('value')})
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


def get_args():
    parser = argparse.ArgumentParser(description='Get Token for a User')
    parser.add_argument('--url', '-e', required=True,
                        help='''CSP Url, example - https://console-dev.cloud.vmware.com ''',
                        default='https://console-dev.cloud.vmware.com')
    parser.add_argument('--user_email', '-u', required=True, help='User Email', default='e2e_fund_pbi@harakirimail.com')
    parser.add_argument('--password', '-p', required=True, help='Password', default='Test@123')
    parser.add_argument('--type', '-t', required=False,
                        help='Type of token - access_token, id_token, refresh_token, all',
                        default='access_token')
    return parser.parse_args()


if __name__ == '__main__':
    CSP_URL = "https://console-preview.cloud.vmware.com"
    INPUT_API_TOKENS_FILE = "preview_300x_users.csv"
    OUTPUT_API_TOKEN_FILE = "preview_300x_users_updated.csv"

    token = AuthToken()

    with open(INPUT_API_TOKENS_FILE) as api_token_reader:
        csv_reader = csv.DictReader(api_token_reader)
        with open(OUTPUT_API_TOKEN_FILE, 'w', newline='\n') as api_token_writer:
            csv_writer = csv.DictWriter(api_token_writer, fieldnames=csv_reader.fieldnames)
            csv_writer.writeheader()

            for user_row in csv_reader:
                REQUEST_SESSION = requests.session()
                mylog.debug("processing user={}".format(user_row))
                fetched_access_token = token.generate_auth_token(CSP_URL, user_row.get('user'), user_row.get('password'))
                # mylog.info("fetched_access_token={}".format(fetched_access_token))

                token.clean_all_api_tokens(CSP_URL, user_row.get('user'), fetched_access_token)
                new_api_token = token.create_new_api_token(CSP_URL, user_row.get('user'), fetched_access_token)
                mylog.info("new_api_token={}".format(new_api_token))

                user_row['refreshToken'] = new_api_token
                csv_writer.writerow(user_row)
                mylog.debug("processing done for user={}".format(user_row.get('user')))

