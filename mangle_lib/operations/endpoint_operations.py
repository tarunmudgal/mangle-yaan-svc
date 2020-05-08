"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""
from mangle_lib.endpoints import *
from commons import utilities
from commons import logger
import os, sys
log = logger.setup_logging(__name__)


class EndpointOperations(object):
    """
    This class contains operations related to Endpoints
    """
    def setup_fault_infra(self, mangle_seesion_obj, k8s_endpoint,
                          k8s_credential, k8s_namespace,
                          ep_name):
        """
        Create a setup like create endpoint endpoint if doesn't exist
        """
        endpoints_obj = Endpoints(mangle_seesion_obj)
        endpoint_credential_obj = EndpointCredential(mangle_seesion_obj)
        test_connection_obj = TestConnection(mangle_seesion_obj)
        log.banner("%s *** Creating Endpoint Credential ***",
                   logger.plugin_name)
        log.debug("%s *** endpoint credential name is '%s' ***",
                  logger.plugin_name, k8s_credential)
        # Creating new endpoint credential if does not exist
        if self.is_endpoint_credential_exist(endpoint_credential_obj,
                                             k8s_credential):
            log.debug("%s *** Endpoint credential %s already exists. Skipping"
                      " creating it ***", logger.plugin_name, k8s_endpoint)
        else:
            kubeconfig_dir = [os.path.join(file + '/config/') for file in sys.path if
                              file.endswith('mangle-yaan-service')][0]
            multipart_form_data = [('kubeConfig', open(kubeconfig_dir+ep_name+'.yaml','rb'))]
            status, output = endpoint_credential_obj.create(
                k8s_credential, multipart_form_data)
            print(output)
            log.debug("%s *** output of endpoint credential create obj ***"
                      " \n %s", logger.plugin_name, output )

            # Creating payload for endpoint and testconnetion
            payload = '{"name": "%s", "endPointType": "K8S_CLUSTER",' \
                      '"credentialsName": "%s",' \
                      '"k8sConnectionProperties": ' \
                      '{"namespace": "%s"}}' % (
                          k8s_endpoint, k8s_credential,k8s_namespace)

            print(payload)
            log.debug("%s *** payload for endpoint & test-connection *** \n %s",
                      logger.plugin_name, payload)

            # Testing connection for endpoint credential
            log.banner("%s *** Testing Endpoint Connection ***",
                       logger.plugin_name)
            status, output = test_connection_obj.create(payload)
            if status:
                self.wait_for_endpoint_credential_to_create(
                    endpoint_credential_obj, k8s_credential)

            # Creating endpoint if does not exist
            log.banner("%s *** Creating Endpoint ***", logger.plugin_name)
            if self.is_endpoint_exist(endpoints_obj, k8s_endpoint):
                log.debug("%s *** Endpoint %s already exists. Skipping creating"
                          " it ***", logger.plugin_name, k8s_endpoint)
            else:
                status, output = endpoints_obj.create(payload)
                log.debug("%s *** output of endpoint create obj *** \n%s",
                          logger.plugin_name, output)

    @utilities.retry(retries=5, exceptions=Exception, sleep=10)
    def is_endpoint_credential_exist(self, endpoint_credential_obj,
                                     endpoint_credential_name):
        """
        Checks if endpoint credential exists
        # TODO : Add try except block
        """
        status, output = endpoint_credential_obj.get()

        found = False
        if status:
            for idx, output_dict in enumerate(output):
                if endpoint_credential_name in output[idx]["name"]:
                    found = True
        return found

    @utilities.retry(retries=5, exceptions=Exception, sleep=10)
    def delete_endpoint_credential(self, endpoint_credential_obj,
                                   endpoint_credential_name):
        """
        Checks if endpoint credential exists
        # TODO : Add try except block
        """
        status, output = endpoint_credential_obj.delete(
            endpoint_credential_name)

        if not status:
            log.error("%s *** DELETE endpoint credential API FAILED with"
                      " output *** \n %s", logger.plugin_name, output)

        if not self.is_endpoint_credential_exist(endpoint_credential_obj,
                                                 endpoint_credential_name):
            log.debug("%s *** Endpoint credential %s deletion SUCCESSFUL ***",
                      logger.plugin_name, endpoint_credential_name)

    @utilities.retry(retries=5, exceptions=Exception, sleep=10)
    def is_endpoint_exist(self, endpoints_obj, endpoint_name):
        """
        Checks if endpoint exists
        # TODO : Add try except block
        """
        status, output = endpoints_obj.get()

        found = False
        if status:
            for output_dict in output:
                if endpoint_name in output_dict["name"]:
                    found = True
        return found

    @utilities.retry(retries=5, exceptions=Exception, sleep=10)
    def delete_endpoint(self, endpoints_obj, endpoint_name):
        """
        Deleted the given endpoint
        # TODO : Add try except block
        """
        status, output = endpoints_obj.delete(endpoint_name)

        if not status:
            log.error("%s *** DELETE endpoint API FAILED with output ***"
                      " \n %s", logger.plugin_name, output)

        if not self.is_endpoint_exist(endpoints_obj, endpoint_name):
            log.debug("%s *** Endpoint %s deletion SUCCESSFUL ***",
                      logger.plugin_name, endpoint_name)

    def wait_for_endpoint_credential_to_create(self, endpoint_credential_obj,
                                               endpoint_credential_name):
        """
        Wait for endpoint credential to create
        # TODO : Add try except block
        """
        found = 0
        retry = 0
        while retry in range(10):
            status, output = endpoint_credential_obj.get()
            log.info(output)
            if status:
                for item in range(len(output)):
                    if endpoint_credential_name in output[item]['name']:
                        log.debug("%s *** endpoint '%s' created successfully"
                                  " ***", logger.plugin_name,
                                  endpoint_credential_name)
                        found = 1
                        break

                if found == 1:
                    break
                retry += 1
                log.debug("%s *** Waiting for endpoint creation to finish ***",
                          logger.plugin_name)
