# Kubernetes Integration

Since MangleYaan operates as a resiliency test framework for Kubernetes (K8s) microservices, direct integration with the Kubernetes control plane is essential.

## K8s Client (`lib/k8s/k8s_client.py`)

The framework implements a dedicated Kubernetes client. The purpose of this client is *not* to inject faults (that is Mangle's job), but rather to **validate state** before, during, and after a chaos experiment.

### Key Responsibilities

1. **Authentication**: The client authenticates with target clusters using the `kubeconfig` details provided by MaximGun at runtime.
2. **Resource Observation**: Tests use the client to query the cluster state. For instance:
   - "Are all pods in the `commerce` namespace in a `Running` state?"
   - "Does the `frontend` Deployment have 3 ready replicas?"
3. **Resiliency Validation**: When a fault is injected (like killing a pod), the K8s client is used in polling loops to verify self-healing. It watches the ReplicaSet to confirm that a replacement pod is spun up and successfully transitions to a `Ready` state within the expected SLA time frame.

By abstracting these operations into a dedicated `K8SClient`, test writers do not need to deal with the complexities of the official Python Kubernetes client directly, but can instead call high-level verification methods.
