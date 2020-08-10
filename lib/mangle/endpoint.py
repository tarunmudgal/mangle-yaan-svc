"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""
import os

from lib.mangle import resources
from lib.common import utils


class EndPointBase(object):
    def __init__(self, mangle_client):
        self.mangle_client = mangle_client


class Endpoint(EndPointBase):
    """
    This class contains CRUD methods related to Endpoint
    """

    @utils.verify_status()
    def create_endpoint_k8s_cluster(self, endpoint_name, credential_name, namespace):
        """
        Creates endpoint
        :param payload: payload in dict
        :return:
        """
        request_body = {
            "name": endpoint_name,
            "endPointType": "K8S_CLUSTER",
            "credentialsName": credential_name,
            "k8sConnectionProperties": {
                "namespace": namespace
            }
        }
        return self.mangle_client.make_call("POST", resources.EP_CTRLR.get('ENDPOINTS'), json=request_body)

    @utils.verify_status()
    def delete_endpoint_k8s_cluster(self, endpoint_name):
        """
        Deletes Endpoint
        :param endpoint_name: name of the endpoint to delete
        :return:
        """
        params = {'endpointNames': endpoint_name}
        return self.mangle_client.make_call("DELETE", resources.EP_CTRLR.get('ENDPOINTS'), params=params)

    @utils.verify_status()
    def get_endpoint_k8s_cluster(self, endpoint_name):
        """
        Gets endpoint details
        :return:
        """
        api_resource = resources.EP_CTRLR.get('ENDPOINTS') + '/' + endpoint_name
        return self.mangle_client.make_call("GET", api_resource)


class EndpointCredential(EndPointBase):
    """
    This class contains methods related to endpoint credentials
    """

    @utils.verify_status()
    def create_credential_k8s_cluster(self, credential_name, kubeconfig_filename):
        """
        Creates endpoint credentials for kubernetes cluster
        :return:
        """
        # kubeconfig_filename = myconfig.get('k8sCluster').get('kubeConfigFileName')
        kubeconfig_filepath = ROOT_DIR + os.path.sep + 'config' + os.path.sep + kubeconfig_filename
        multipart_form_data = [("kubeConfig", open(kubeconfig_filepath, "rb"))]
        params = {'id': credential_name, 'name': credential_name}
        import pdb; pdb.set_trace()
        return self.mangle_client.make_call("POST", resources.EP_CTRLR.get('K8S_CREDENTIALS'),
                                            files=multipart_form_data, params=params)

    @utils.verify_status()
    def delete_credential(self, credential_name):
        """
        Deletes endpoint credentials for kubernetes cluster
        :return:
        """
        params = {'credentialNames': credential_name}
        return self.mangle_client.make_call("DELETE", resources.EP_CTRLR.get('CREDENTIALS'), params=params)

    @utils.verify_status()
    def get_credentials(self):
        """
        Gives endpoint credential details
        """
        return self.mangle_client.make_call("GET", resources.EP_CTRLR.get('CREDENTIALS'))


class TestConnection(EndPointBase):
    """
    This class contains methods related to test connection for endpoint
    """

    @utils.verify_status()
    def test_connection(self, endpoint_name):
        """
        Tests connection for endpoint
        :param payload: payload in dict
        :return:
        """
        params = {'endpointNames': endpoint_name}
        return self.mangle_client.make_call("POST", resources.EP_CTRLR.get('TEST_CONNECTION'), params=params)
