"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""


class Common(object):

    def __init__(self, mangle_api):
        self.mangle_api = mangle_api
        self.api_endpoint = "/endpoints"


class Endpoints(Common):
    """
    This class contains CRUD methods related to Endpoint
    """
    def create(self, payload):
        """
        Creates endpoint
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send("POST", self.api_endpoint, data=payload)

    def get(self):
        """
        Gets endpoint details
        :return:
        """
        return self.mangle_api.send("GET", self.api_endpoint)

    def delete(self, endpoint_name):
        """
        Deletes Endpoint
        :param endpoint_name: name of the endpoint to delete
        :return:
        """
        api_endpoint = "{0}?endpointNames={1}".\
            format(self.api_endpoint, endpoint_name)
        return self.mangle_api.send("DELETE", api_endpoint)

    def update(self, payload):
        """
        Update Endpoint
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send("PUT", self.api_endpoint, data=payload)


class EndpointCredential(Common):
    """
    This class contains methods related to endpoint credentials
    """

    def create(self, endpoint_credential_name, mp_username, mp_password):
        """
        Creates endpoint credentials
        :return:
        """
        api_endpoint = "{0}/credentials/remotemachine?name={1}" \
                       "&password={2}&username={3}".\
            format(self.api_endpoint, endpoint_credential_name, mp_password,
                   mp_username)
        return self.mangle_api.send("POST", api_endpoint)

    def delete(self, endpoint_credential_name):
        """
        Deletes endpoint credentials
        :return:
        """
        api_endpoint = "{0}/credentials?credentialNames={1}".\
            format(self.api_endpoint, endpoint_credential_name)
        return self.mangle_api.send("DELETE", api_endpoint)

    def get(self):
        """
        Gives endpoint credential details
        """
        api_endpoint = "{0}/credentials".format(self.api_endpoint)
        return self.mangle_api.send("GET", api_endpoint)


class TestConnection(Common):
    """
    This class contains methods related to test connection for endpoint
    """

    def create(self, payload):
        """
        Tests connection for endpoint
        :param payload: payload in dict
        :return:
        """
        api_endpoint = "{0}/testEndpoint".format(self.api_endpoint)
        return self.mangle_api.send("POST", api_endpoint, data=payload)
