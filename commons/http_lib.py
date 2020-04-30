import logging
import requests
import urllib3

log = logging.getLogger(__name__)
HTTPError = requests.exceptions.HTTPError


class Session(requests.Session):
    """
    inherited the requests.session
    """

    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.mangle_default_timeout = None

    def request(self, *args, **kwargs):
        if not kwargs.get('timeout'):
            kwargs['timeout'] = self.mangle_default_timeout
        r = super(Session, self).request(*args, **kwargs)
        return r


def send(verb, url, session_, **kwargs):
    """
    Send a HTTP request

    Parameters
    ----------
    verb: string
        HTTP verb; 'GET', 'POST', 'PUT', 'DELETE'
    url: string
        URL server api
        (https://{mangle-ip/hostname}/mangle-services/rest/api/v1/cluster-config)
    session_: object
        session object to whom we want to connect
    kwargs: dict
        Any extra keyword arguments requests.request accepts.
        See http://docs.python-requests.org/en/master/api/#requests.request

    Returns
    -------
    response object
    """

    response = session_.request(verb, url, **kwargs)
    return response
