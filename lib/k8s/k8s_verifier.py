import os

from lib.k8s import k8s_client


class K8SVerifier(object):
    def verfy_k8s(kube_config_file, namespace):

        verify = k8s_client.K8SClient(kube_config_file, namespace)
        list_pod = verify.get_pods()
        for i in list_pod.items:
            try:
                assert i.status.phase == "Running", i.metadata.name + " is Running"
                print("%s is Running" % (i.metadata.name))
            except AssertionError as msg:
                print(msg)


if __name__ == "__main__":
    kube_config_file = os.environ.get(
        "KUBECONFIG", "/Users/bverma/Downloads/scdc1-staging-trace-it-now.yaml"
    )
    namespace = "scdc1-staging-trace-it-now"
    K8SVerifier.verfy_k8s(kube_config_file, namespace)
