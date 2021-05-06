import os
import time
import typing

import yaml
from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException


class K8SClient:
    """
    Kubernetes client wrapper APIs that can manage CSP K8S infra.
    Refer kubernetes-client API doc here- https://github.com/kubernetes-client/python/tree/master/kubernetes
    """

    __single_instance = None

    def __init__(self, kubeconfig_filename, namespace):

        if K8SClient.__single_instance is not None:
            raise Exception("K8SClient is a singleton class and cannot have more than one objects")

        K8SClient.__single_instance = self

        if not os.path.isabs(kubeconfig_filename):
            kubeconfig_dir = ROOT_DIR + os.path.sep + "config" + os.path.sep + "kubeconfigs"
            self.kubeconfig_filepath = kubeconfig_dir + os.path.sep + kubeconfig_filename
        else:
            self.kubeconfig_filepath = kubeconfig_filename
        self.csp_k8s_dir = ROOT_DIR + os.path.sep + "infra" + os.path.sep + "csp_k8s"

        self.namespace = namespace
        config.load_kube_config(config_file=self.kubeconfig_filepath)
        self.core_v1_api_client = client.CoreV1Api()
        self.api_client = client.ApiClient()
        self.networking_v1_api = client.NetworkingV1Api(self.api_client)
        self.apps_v1_api = client.AppsV1Api(self.api_client)

    def get_pods(self, **kwargs: str) -> typing.List[str]:
        """lists pods from the namespace used while creating k8s client.
        it simply calls list_namespaced_pod API that supports below kwargs-
        :param async_req bool
        :param str namespace: object name and auth scope, such as for teams and projects (required)
        :param str pretty: If 'true', then the output is pretty printed.
        :param bool allow_watch_bookmarks: allowWatchBookmarks requests watch events with type \"BOOKMARK\". Servers that do not implement bookmarks may ignore this flag and bookmarks are sent at the server's discretion. Clients should not assume bookmarks are returned at any specific interval, nor may they assume the server will send any BOOKMARK event during a session. If this is not a watch, this field is ignored. If the feature gate WatchBookmarks is not enabled in apiserver, this field is ignored.  This field is alpha and can be changed or removed without notice.
        :param str _continue: The continue option should be set when retrieving more results from the server. Since this value is server defined, clients may only use the continue value from a previous query result with identical query parameters (except for the value of continue) and the server may reject a continue value it does not recognize. If the specified continue value is no longer valid whether due to expiration (generally five to fifteen minutes) or a configuration change on the server, the server will respond with a 410 ResourceExpired error together with a continue token. If the client needs a consistent list, it must restart their list without the continue field. Otherwise, the client may send another list request with the token received with the 410 error, the server will respond with a list starting from the next key, but from the latest snapshot, which is inconsistent from the previous list results - objects that are created, modified, or deleted after the first list request will be included in the response, as long as their keys are after the \"next key\".  This field is not supported when watch is true. Clients may start a watch from the last resourceVersion value returned by the server and not miss any modifications.
        :param str field_selector: A selector to restrict the list of returned objects by their fields. Defaults to everything.
        :param str label_selector: A selector to restrict the list of returned objects by their labels. Defaults to everything.
        :param int limit: limit is a maximum number of responses to return for a list call. If more items exist, the server will set the `continue` field on the list metadata to a value that can be used with the same initial query to retrieve the next set of results. Setting a limit may return fewer than the requested amount of items (up to zero items) in the event all requested objects are filtered out and clients should only use the presence of the continue field to determine whether more results are available. Servers may choose not to support the limit argument and will return all of the available results. If limit is specified and the continue field is empty, clients may assume that no more results are available. This field is not supported if watch is true.  The server guarantees that the objects returned when using continue will be identical to issuing a single list call without a limit - that is, no objects created, modified, or deleted after the first request is issued will be included in any subsequent continued requests. This is sometimes referred to as a consistent snapshot, and ensures that a client that is using limit to receive smaller chunks of a very large result can ensure they see all possible objects. If objects are updated during a chunked list the version of the object that was present at the time the first list result was calculated is returned.
        :param str resource_version: When specified with a watch call, shows changes that occur after that particular version of a resource. Defaults to changes from the beginning of history. When specified for list: - if unset, then the result is returned from remote storage based on quorum-read flag; - if it's 0, then we simply return what we currently have in cache, no guarantee; - if set to non zero, then the result is at least as fresh as given rv.
        :param int timeout_seconds: Timeout for the list/watch call. This limits the duration of the call, regardless of any activity or inactivity.
        :param bool watch: Watch for changes to the described resources and return them as a stream of add, update, and remove notifications. Specify resourceVersion.
        :return: V1PodList
                 If the method is called asynchronously,
                 returns the request thread.
        """
        mylog.info("listing pods from {} namespace with following options={}".format(self.namespace, kwargs))
        try:
            ret = self.core_v1_api_client.list_namespaced_pod(self.namespace, **kwargs)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while listing pods from namespace={}. Exception={}".format(
                    self.namespace, fault
                )
            )

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

    def execute_cmd_inside_pod(self, pod_name, cmd):

        exec_command = ['/bin/sh', '-c', cmd]
        try:
            resp = stream(self.core_v1_api_client.connect_get_namespaced_pod_exec,
                          pod_name,
                          'csp-app-preview', command=exec_command, stderr=True, stdout=True, stdin=False,
                          tty=False)
            return resp
        except ApiException as fault:
            mylog.exception(
                "Exception occurred while executing command='{}' inside pod={}".format(exec_command, pod_name)
            )

    def wait_for_pods_to_update_state(self, new_replica_count, timeout=600, sleep_interval=10, **kwargs):
        replica_count = -1
        start_time = curr_time = time.time()
        while replica_count != new_replica_count and curr_time < start_time + timeout:
            pods_resp = self.get_pods(**kwargs)
            pod_names = [item.metadata.name for item in pods_resp.items if item.status.phase ==
                                     "Running"]
            replica_count = len(pod_names)
            mylog.info(
                "currently {} pod(s) seem to be running. Expected pod(s) count is {}".format(
                    replica_count, new_replica_count
                )
            )

            if replica_count == new_replica_count:
                mylog.info(
                    "pods updated with {} replica count".format(
                        replica_count
                    )
                )
                return True, pod_names

            time.sleep(sleep_interval)
            curr_time = time.time()

        return False, []



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

    def get_deployment(self, deployment_name: str) -> client.V1Deployment:
        """
        reads a deployment details
        Args:
            deployment_name: deployment name for which details are required

        Returns:
            client.V1Deployment object
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
                    deployment_name, fault
                )
            )

        return response

    def scale_deployment(
        self,
        deployment_name: str,
        new_replica_count: int,
        timeout: int = 360,
        sleep_interval: int = 10,
    ) -> bool:
        """
        updates a deployment replica count
        Args:
            deployment_name: deployment name that needs to be scaled to new_replica_count
            new_replica_count: new replica count to be set for the deployment_name. It can be used to scale up/down a deployment
            timeout: timeout in seconds to wait for deployement to adapt new_replica_count
            sleep_interval: polling interval to check replicas count if deployment adapted new_replica_count

        Returns:
            True if deployment reached to new_replica_count before timeout period else False
        """

        mylog.info(
            "deployment {} is going to be scaled to {} replicas".format(
                deployment_name, new_replica_count
            )
        )

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
                    deployment_name, fault
                )
            )

        available_replicas = -1
        start_time = curr_time = time.time()
        while available_replicas != new_replica_count and curr_time < start_time + timeout:
            deployment_info = self.get_deployment(deployment_name)
            available_replicas = (
                0
                if deployment_info.status.available_replicas is None
                else deployment_info.status.available_replicas
            )
            mylog.info(
                "deployment {} got {} available replicas currently".format(
                    deployment_name, available_replicas
                )
            )

            if available_replicas == new_replica_count:
                mylog.info(
                    "deployment {} updated with {} available_replicas".format(
                        deployment_name, new_replica_count
                    )
                )
                return True

            time.sleep(sleep_interval)
            curr_time = time.time()

        return False

    def scale_deployments(
        self, deployments_replica_map: dict, timeout: int = 900, sleep_interval: int = 30,
    ) -> tuple:
        """
        updates deployments replica count
        Args:
            deployments_replica_map: a dict of diployment name and new_replica count. It can be used to scale up/down different deployments
            timeout: timeout in seconds to wait for all the deployements to adapt associated replica count
            sleep_interval: polling interval to check replicas count if all deployments adapted associated replica count

        Returns:
            (True, []) if all deployments reached to their associated replica count before timeout period else (
            False, [deployments_failed_to_be_scaled])
        """

        mylog.info(
            "following deployments are going to be scaled to their associated replica count: {}".format(
                deployments_replica_map
            )
        )

        deployments_scaled_successfully = []
        deployments_not_yet_scaled = list(deployments_replica_map.keys())

        for deployment_name, deployment_replica_count in deployments_replica_map.items():
            deployment_info = self.get_deployment(deployment_name)
            deployment_info.spec.replicas = deployment_replica_count
            try:
                self.apps_v1_api.patch_namespaced_deployment_scale(
                    deployment_name, self.namespace, deployment_info, pretty="true"
                )
                # mylog.info(response)
            except ApiException as fault:
                mylog.exception(
                    "exception occurred while reading deployment details for deployment name={}. Exception={}".format(
                        deployment_name, fault
                    )
                )

        start_time = curr_time = time.time()
        while deployments_not_yet_scaled and curr_time < start_time + timeout:
            for deployment_name in deployments_not_yet_scaled:
                deployment_info = self.get_deployment(deployment_name)
                available_replicas = (
                    0
                    if deployment_info.status.available_replicas is None
                    else deployment_info.status.available_replicas
                )
                if available_replicas == deployments_replica_map[deployment_name]:
                    mylog.info(
                        "deployment {} updated with {} available_replicas successfully".format(
                            deployment_name, available_replicas
                        )
                    )
                    deployments_not_yet_scaled.remove(deployment_name)
                    deployments_scaled_successfully.append(deployment_name)
                else:
                    mylog.info(
                        "deployment={}, available_replicas={}, expected_replicas={}. waiting for {} seconds".format(
                            deployment_name,
                            available_replicas,
                            deployments_replica_map[deployment_name],
                            sleep_interval,
                        )
                    )

            time.sleep(sleep_interval)
            curr_time = time.time()

        if not deployments_not_yet_scaled:
            return True, []

        return False, deployments_not_yet_scaled

    def get_service(self, service_name: str) -> client.V1Service:
        """
        reads a service details
        Args:
            service_name: service name for which details are required

        Returns:
            client.V1Service object
        """

        mylog.info("reading service details for service name={}".format(service_name))

        response = None
        try:
            response = self.core_v1_api_client.read_namespaced_service(
                service_name, self.namespace, pretty="true"
            )
            # mylog.info(response)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while reading service details for service name={}. Exception={}".format(
                    service_name, fault
                )
            )

        return response

    def list_services(self) -> client.V1ServiceList:
        """
        lists all services within a namespace

        Returns:
            List of services
        """

        mylog.info("listing all services where namespace={}".format(self.namespace))

        response = None
        try:
            response = self.core_v1_api_client.list_namespaced_service(
                self.namespace, pretty="true"
            )
            # mylog.info(response)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while listing services from namespace={}. Exception={}".format(
                    self.namespace, fault
                )
            )

        return response

    def patch_service(self, service_name: str, body: client.V1Service) -> client.V1Service:
        """
        patches a service
        Args:
            service_name: service name for which details are required
            body: updated (with patch changes) client.V1Service object

        Returns:
            client.V1Service object
        """

        mylog.info("patching service details for service name={}".format(service_name))

        response = None
        try:
            response = self.core_v1_api_client.patch_namespaced_service(
                service_name, self.namespace, body, pretty="true"
            )
            # mylog.info(response)
        except ApiException as fault:
            mylog.exception(
                "exception occurred while patching service details for service name={}. Exception={}".format(
                    service_name, fault
                )
            )

        return response

    def create_network_policy(self, network_policy_fname):
        network_policy_fpath = (
            self.csp_k8s_dir + os.path.sep + "networkpolicy" + os.path.sep + network_policy_fname
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
                network_policy_name,
                self.namespace,
                pretty="true",
                grace_period_seconds=0,
                body=body,
            )
        except ApiException as fault:
            mylog.exception(
                "exception occurred while deleting NetworkPolicy {}. Exception={}".format(
                    network_policy_name, fault
                )
            )

        return response
