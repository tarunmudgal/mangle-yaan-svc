import os
import typing

import yaml
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class K8SClient(object):
    def __init__(self, kubeconfig_filename, namespace):
        kubeconfig_dir = ROOT_DIR + os.path.sep + "config" + os.path.sep + "kubeconfigs"
        self.kubeconfig_filepath = kubeconfig_dir + os.path.sep + kubeconfig_filename
        self.csp_k8s_dir = ROOT_DIR + os.path.sep + "infra" + os.path.sep + "csp_k8s"

        self.namespace = namespace
        config.load_kube_config(config_file=self.kubeconfig_filepath)
        self.core_v1_api_client = client.CoreV1Api()
        self.api_client = client.ApiClient()
        self.networking_v1_api = client.NetworkingV1Api(self.api_client)
        self.apps_v1_api = client.AppsV1Api(self.api_client)

    def get_pods(self) -> typing.List[str]:
        mylog.info("listing all pods in {} namespace".format(self.namespace))
        ret = self.core_v1_api_client.list_namespaced_pod(self.namespace)
        return ret

    def delete_pod(self, pod_name: str) -> None:
        """Deletes POD"""
        try:
            self.core_v1_api_client.delete_namespaced_pod(
                pod_name, self.namespace, body=client.V1DeleteOptions()
            )
        except ApiException as e:
            # If the pod is already deleted
            if e.status != 404:
                raise

    def deploy_deployment(self, deployment_fname, app_name, args, labels):
        """
        Deploys a deployment
        """
        deployment_filepath = (
                self.csp_k8s_dir + os.path.sep + "deployment" + os.path.sep + deployment_fname
        )
        mylog.info("deployment started using {} deployment file".format(deployment_filepath))

        with open(deployment_filepath) as f:
            payload = yaml.load(f)

        try:
            api_response = self.apps_v1_api.read_namespaced_deployment(
                self.namespace, payload, pretty=True
            )
            mylog.info(api_response)
        except ApiException as fault:
            mylog.exception(
                "Exception when calling ExtensionsV1beta1Api->create_namespaced_deployment: %s\n"
                % fault
            )

        return payload["spec"]["template"]["spec"]["containers"][0]["ports"][0]["containerPort"]

    def get_deployment(self, deployment_name):
        """
        reads a deployment details
        """

        mylog.info("reading deployment details for deployment name={}".format(deployment_name))

        response = None
        try:
            response = self.apps_v1_api.read_namespaced_deployment(
                deployment_name, self.namespace, pretty="true"
            )
            # mylog.info(response)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while reading deployment details for deployment name={}. Exception={}".format(
                    deployment_name, fault)
            )

        return response

    def scale_deployment(self, deployment_name, new_replica_count, timeout=360, sleep_interval=10):
        """
        updates a deployment replica count
        """

        deployment_info = self.get_deployment(deployment_name)
        deployment_info.spec.replicas = new_replica_count

        try:
            self.apps_v1_api.patch_namespaced_deployment_scale(
                deployment_name, self.namespace, deployment_info, pretty="true"
            )
            # mylog.info(response)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while reading deployment details for deployment name={}. Exception={}".format(
                    deployment_name, fault)
            )

        available_replicas = -1
        start_time = curr_time = time.time()
        while available_replicas != new_replica_count and curr_time < start_time + timeout:
            deployment_info = self.get_deployment(deployment_name)
            available_replicas = deployment_info.status.available_replicas
            mylog.info("deployment {} got {} available replicas currently".format(deployment_name, available_replicas))

            if available_replicas == new_replica_count:
                mylog.info("deployment {} updated with {} available_replicas".format(deployment_name, new_replica_count))
                return True

            time.sleep(sleep_interval)
            curr_time = time.time()

        return False

    def create_network_policy(self, network_policy_fname):
        network_policy_fpath = (
                self.csp_k8s_dir
                + os.path.sep
                + "networkpolicy"
                + os.path.sep
                + network_policy_fname
        )
        with open(network_policy_fpath) as fh:
            network_policy_fdata = yaml.load(fh, Loader=yaml.FullLoader)

        body = client.V1NetworkPolicy(
            api_version=network_policy_fdata["apiVersion"],
            kind=network_policy_fdata["kind"],
            metadata=network_policy_fdata["metadata"],
            spec=network_policy_fdata["spec"],
        )

        response = None
        try:
            response = self.networking_v1_api.create_namespaced_network_policy(
                self.namespace, body, pretty="true"
            )
        except ApiException as fault:
            mylog.exception(
                "exception occurred while creating a NetworkPolicy. Exception={}".format(fault)
            )

        return response

    def delete_network_policy(self, network_policy_name):
        body = client.V1DeleteOptions()

        response = None
        try:
            response = self.networking_v1_api.delete_namespaced_network_policy(
                network_policy_name, self.namespace, pretty="true", grace_period_seconds=0, body=body
            )
        except ApiException as fault:
            mylog.exception(
                "exception occurred while deleting NetworkPolicy {}. Exception={}".format(
                    network_policy_name, fault
                )
            )

        return response
