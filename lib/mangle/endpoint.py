"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""
import os
import sys

from lib.common import utils
from lib.mangle import mangle_client, resources


endpoint_cred_obj = None
endpoint_obj = None
test_connection_obj = None


class EndPointBase:
    def __init__(self, mangle_client):
        self.mangle_client = mangle_client


class Endpoint(EndPointBase):
    """
    This class contains CRUD methods related to Endpoint
    """

    @utils.verify_status(do_log=False)
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
            "k8sConnectionProperties": {"namespace": namespace},
        }
        return self.mangle_client.make_call(
            "POST", resources.EP_CTRLR.get("ENDPOINTS"), json=request_body
        )

    @utils.verify_status(do_log=False)
    def delete_endpoint_k8s_cluster(self, endpoint_name):
        """
        Deletes Endpoint
        :param endpoint_name: name of the endpoint to delete
        :return:
        """
        params = {"endpointNames": endpoint_name}
        return self.mangle_client.make_call(
            "DELETE", resources.EP_CTRLR.get("ENDPOINTS"), params=params
        )

    @utils.verify_status(do_log=False)
    def get_endpoint_k8s_cluster(self, endpoint_name):
        """
        Gets endpoint details
        :return:
        """
        api_resource = resources.EP_CTRLR.get("ENDPOINTS") + "/" + endpoint_name
        return self.mangle_client.make_call("GET", api_resource)

    @utils.verify_status(do_log=False)
    def list_endpoints_k8s_cluster(self, credential_name=None):
        """
        Gets endpoint details
        :return:
        """
        params = None
        if credential_name:
            params = {"credentialName": credential_name}
        api_resource = resources.EP_CTRLR.get("ENDPOINTS")

        return self.mangle_client.make_call("GET", api_resource, params=params)


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
        kubeconfig_filepath = (
            ROOT_DIR
            + os.path.sep
            + "config"
            + os.path.sep
            + "kubeconfigs"
            + os.path.sep
            + kubeconfig_filename
        )
        files = [("kubeConfig", open(kubeconfig_filepath, "rb"))]
        params = {"id": credential_name, "name": credential_name}
        api_resource = resources.EP_CTRLR.get("K8S_CREDENTIALS")

        return self.mangle_client.make_call(
            "POST", api_resource, params=params, files=files, data={}
        )

    @utils.verify_status()
    def update_credential_k8s_cluster(self, credential_name, kubeconfig_filename):
        """
        Creates endpoint credentials for kubernetes cluster
        :return:
        """
        kubeconfig_filepath = (
            ROOT_DIR
            + os.path.sep
            + "config"
            + os.path.sep
            + "kubeconfigs"
            + os.path.sep
            + kubeconfig_filename
        )
        files = [("kubeConfig", open(kubeconfig_filepath, "rb"))]
        params = {"id": credential_name, "name": credential_name}
        headers = {"Authorization": "Basic YWRtaW5AbWFuZ2xlLmxvY2FsOmFkbWlu"}
        api_resource = resources.EP_CTRLR.get("K8S_CREDENTIALS")
        # return self.mangle_client.make_call("POST", resources.EP_CTRLR.get('K8S_CREDENTIALS'),
        #                                     files=multipart_form_data, params=params)

        return self.mangle_client.make_call(
            "PUT", api_resource, params=params, headers=headers, files=files, data={}
        )

    @utils.verify_status()
    def delete_credential(self, credential_name):
        """
        Deletes endpoint credentials for kubernetes cluster
        :return:
        """
        params = {"credentialNames": credential_name}
        return self.mangle_client.make_call(
            "DELETE", resources.EP_CTRLR.get("CREDENTIALS"), params=params
        )

    @utils.verify_status()
    def list_credentials(self):
        """
        Gives endpoint credential details
        """
        return self.mangle_client.make_call("GET", resources.EP_CTRLR.get("CREDENTIALS"))


class TestConnection(EndPointBase):
    """
    This class contains methods related to test connection for endpoint
    """

    @utils.verify_status()
    def test_endpoint(self, endpoint_name):
        """
        Tests connection for endpoint
        :param payload: payload in dict
        :return:
        """
        epoint = Endpoint(self.mangle_client)
        status, response = epoint.get_endpoint_k8s_cluster(endpoint_name)
        if status:
            rj = response.json
            payload = {
                "id": rj.get("id"),
                "name": rj.get("name"),
                "endPointType": rj.get("endPointType"),
                "credentialsName": rj.get("credentialsName"),
                "k8sConnectionProperties": rj.get("k8sConnectionProperties"),
            }
            params = {"endpointNames": endpoint_name}
        return self.mangle_client.make_call(
            "POST", resources.EP_CTRLR.get("TEST_ENDPOINT"), json=payload
        )

    @utils.verify_status()
    def test_connection(self, endpoint_name):
        """
        Tests connection for endpoint
        :param payload: payload in dict
        :return:
        """
        params = {"endpointNames": endpoint_name}
        return self.mangle_client.make_call(
            "POST", resources.EP_CTRLR.get("TEST_CONNECTION"), params=params
        )


def _create_credentials_k8s(mclient: mangle_client.MangleClient):
    global endpoint_cred_obj
    if endpoint_cred_obj is None:
        endpoint_cred_obj = EndpointCredential(mclient)

    does_cred_exist = False
    status, response = endpoint_cred_obj.list_credentials()
    if not status:
        mylog.error("Failed to fetch credentials from mangle")
        sys.exit(2)

    for cred in response.json:
        if cred.get("name") == myconfig.get("k8sCluster").get("credentialName"):
            does_cred_exist = True
            break
    if not does_cred_exist:
        status, response = endpoint_cred_obj.create_credential_k8s_cluster(
            myconfig.get("k8sCluster").get("credentialName"),
            myconfig.get("k8sCluster").get("kubeConfigFileName"),
        )
        if not status:
            mylog.error(
                "Failed to create k8s cluster credential for credentialName={}, kubeConfigFileName={}".format(
                    myconfig.get("k8sCluster").get("credentialName"),
                    myconfig.get("k8sCluster").get("kubeConfigFileName"),
                )
            )
            sys.exit(2)
        mylog.info(
            "credential '{}' for k8s cluster created successfully".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )
    else:
        mylog.info(
            "credential '{}' for k8s cluster already exist".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )


def _update_credentials_k8s(mclient: mangle_client.MangleClient):
    global endpoint_cred_obj
    if endpoint_cred_obj is None:
        endpoint_cred_obj = EndpointCredential(mclient)

    does_cred_exist = False
    status, response = endpoint_cred_obj.list_credentials()
    if not status:
        mylog.error("Failed to fetch credentials from mangle")
        sys.exit(2)

    for cred in response.json:
        if cred.get("name") == myconfig.get("k8sCluster").get("credentialName"):
            does_cred_exist = True
            break
    if does_cred_exist:
        status, response = endpoint_cred_obj.update_credential_k8s_cluster(
            myconfig.get("k8sCluster").get("credentialName"),
            myconfig.get("k8sCluster").get("kubeConfigFileName"),
        )
        if not status:
            mylog.error(
                "Failed to update k8s cluster credential for credentialName={}, kubeConfigFileName={}".format(
                    myconfig.get("k8sCluster").get("credentialName"),
                    myconfig.get("k8sCluster").get("kubeConfigFileName"),
                )
            )
            sys.exit(2)
        mylog.info(
            "credential '{}' for k8s cluster updated successfully".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )
    else:
        mylog.info(
            "credential '{}' for k8s cluster does not exist".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )


def _delete_credentials_k8s(mclient: mangle_client.MangleClient):
    global endpoint_cred_obj
    if endpoint_cred_obj is None:
        endpoint_cred_obj = EndpointCredential(mclient)

    does_cred_exist = False
    status, response = endpoint_cred_obj.list_credentials()
    if not status:
        mylog.error("Failed to fetch credentials from mangle")
        sys.exit(2)

    for cred in response.json:
        if cred.get("name") == myconfig.get("k8sCluster").get("credentialName"):
            does_cred_exist = True
            break
    if does_cred_exist:
        status, response = endpoint_cred_obj.delete_credential(
            myconfig.get("k8sCluster").get("credentialName")
        )
        if not status:
            mylog.error(
                "Failed to delete k8s cluster credential for credentialName={}".format(
                    myconfig.get("k8sCluster").get("credentialName")
                )
            )
            sys.exit(2)
        mylog.info(
            "credential '{}' for k8s cluster deleted successfully".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )
    else:
        mylog.info(
            "credential '{}' for k8s cluster does not exist".format(
                myconfig.get("k8sCluster").get("credentialName")
            )
        )


def _create_endpoint_k8s(mclient: mangle_client.MangleClient):
    global endpoint_obj
    if endpoint_obj is None:
        endpoint_obj = Endpoint(mclient)

    does_endpoint_exist = False
    status, response = endpoint_obj.list_endpoints_k8s_cluster()
    if not status:
        mylog.error("Failed to fetch endpoints from mangle")
        sys.exit(2)
    for ep in response.json:
        if ep.get("name") == myconfig.get("k8sCluster").get("endpointName"):
            does_endpoint_exist = True
            break
    if not does_endpoint_exist:
        try:
            status, response = endpoint_obj.create_endpoint_k8s_cluster(
                myconfig.get("k8sCluster").get("endpointName"),
                myconfig.get("k8sCluster").get("credentialName"),
                myconfig.get("k8sCluster").get("namespace"),
            )
        except Exception as fault:
            # fallback for updating credentials as mostly exception occurs due to incorrect credentials
            _update_credentials_k8s(mclient)
            status, response = endpoint_obj.create_endpoint_k8s_cluster(
                myconfig.get("k8sCluster").get("endpointName"),
                myconfig.get("k8sCluster").get("credentialName"),
                myconfig.get("k8sCluster").get("namespace"),
            )
        if not status:
            mylog.error(
                "Failed to create k8s cluster endpoint for endpointName={}, credentialName={}, namespace={}".format(
                    myconfig.get("k8sCluster").get("endpointName"),
                    myconfig.get("k8sCluster").get("credentialName"),
                    myconfig.get("k8sCluster").get("namespace"),
                )
            )
            sys.exit(2)
        mylog.info(
            "endpoint '{}' for k8s cluster created successfully".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )
    else:
        mylog.info(
            "Endpoint '{}' for k8s cluster already exist".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )


def _test_endpoint_k8s(mclient: mangle_client.MangleClient):
    global test_connection_obj
    if test_connection_obj is None:
        test_connection_obj = TestConnection(mclient)

    try:
        status, response = test_connection_obj.test_endpoint(
            myconfig.get("k8sCluster").get("endpointName")
        )
    except Exception as fault:
        # fallback for updating credentials as mostly exception occurs due to incorrect credentials
        _update_credentials_k8s(mclient)
        status, response = test_connection_obj.test_endpoint(
            myconfig.get("k8sCluster").get("endpointName")
        )

    if not status:
        mylog.error(
            "Test connection for endpoint {} failed".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )
        sys.exit(2)
    else:
        mylog.info(
            "Test connection for endpoint {} passed".format(
                myconfig.get("k8sCluster").get("endpointName")
            )
        )


def create_and_test_mangle_endpoint(mclient: mangle_client.MangleClient):
    _create_credentials_k8s(mclient)
    _create_endpoint_k8s(mclient)
    _test_endpoint_k8s(mclient)
