import requests
import urllib3
import json
from commons import logger
from commons import http_lib
# lib_path = os.path.abspath(os.path.join(__file__, '..', '..', '..','infrastructure'))
# sys.path.append(lib_path)
# import http_lib

log = logger.setup_logging(__name__)

class MangleApi(object):
    """
    Wrapper to interact with the Mangle REST API's

    Parameters
    ----------
    hostname: string
        IP Address or FQDN to Mangle
    username: string
        Mangle username
    password: string
        Mangle password
    prefix: string
        API prefix (will be append to the hostname)
    ssl_verify: bool, optional
        Perform SSL host verification (default=False)
    """

    def __init__(self, hostname, username, password,
                 prefix="/mangle-services/rest/api/v1", ssl_verify=False):
        """Init Mangle API with hostname and login credentials."""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.prefix = prefix

        self._session = http_lib.Session()
        self._session.auth = self.username, self.password
        self._session.verify = ssl_verify
        if not ssl_verify:
            urllib3.disable_warnings()

    def __repr__(self):
        return 'MANGLEAPI(%r, %r, %r, %r)' % (self.hostname, self.username,
                                              self.password, self.prefix)

    def send(self, verb, ep_name, prefix=None,files=None, headers=None, **kwargs):
        """
        verb: string
        HTTP verb; 'GET', 'POST', 'PUT', 'DELETE'

        ep_name : string
            endpoint name, like (cluster-config)
            (https://{mangle-ip/hostname}/mangle-services/rest/api/v1/cluster-config)

        prefix: String
            default prefix is: "/mangle-services/rest/api/v1"

        kwargs: dict

        Returns
        --------
        will return True with api's json content on success else false with
                                                    respective cause of failure
        """
        if files is not None:
            kwargs['files']=files
        kwargs['headers'] = headers
        if headers is None:
            kwargs['headers'] = {'Content-type': 'application/json'}

        prefix = self.prefix if prefix is None else prefix
        url = "".join(["https://", self.hostname, prefix, ep_name])
        log.debug("%s *** Running URL %s %s ***", logger.plugin_name, verb, url)
        status_code_dict = {
            401: "unauthorized access",
            403: "forbidden",
            404: "not found"
        }
        response = None
        try:
            response = http_lib.send(verb, url, self._session, **kwargs)
            json_response = response.json()
            log.debug("%s *** %s API response %s = \n %s",
                      logger.plugin_name, verb, ep_name, json_response)
            return True, json_response
        except Exception as error:
            # TODO: check what response.content returns then change logging accordingly
            log.error("%s %s", logger.plugin_name, error)
            log.error("%s Error - %s", logger.plugin_name, response.content)
            if response.status_code in status_code_dict.keys():
                log.error("%s *** API %s failed. \nResponse %s - %s",
                          logger.plugin_name, ep_name, response.status_code,
                          status_code_dict[response.status_code])
            else:
                log.error("%s *** API %s failed. Response %s - unknown"
                          " error code. ***", logger.plugin_name, ep_name,
                          response.status_code)
            raise
