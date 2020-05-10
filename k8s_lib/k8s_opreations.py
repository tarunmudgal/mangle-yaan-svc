from kubernetes import client, config
from time import sleep
from kubernetes.client.rest import ApiException

class K8SOperation(object):



    def __init__(self,config_file,namespace):

        self.kube_config_file=config_file
        self.namespace=namespace

    def get_k8s_pod_in_namespace(self):
        config.load_kube_config(config_file=self.kube_config_file)
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs:")
        ret = v1.list_namespaced_pod(self.namespace)
        return ret

    def delete_pod(self, pod_id: str) -> None:
        """Deletes POD"""
        try:
            self.kube_client.delete_namespaced_pod(
                pod_id, self.namespace, body=client.V1DeleteOptions(),
                **self.kube_config.kube_client_request_args)
        except ApiException as e:
            # If the pod is already deleted
            if e.status != 404:
                raise


