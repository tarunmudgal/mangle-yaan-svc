# Chaos Engineering Quickstart

## What is Chaos Engineering?
Chaos Engineering is the discipline of experimenting on a system in order to build confidence in the system's capability to withstand turbulent conditions in production. Instead of waiting for outages to happen, chaos engineering proactively injects failures into a system to ensure that the system recovers gracefully.

## What is a "Fault"?
In the context of the **MangleYaan** framework, a **fault** is a deliberate disruption introduced into a target environment. Faults can occur at different layers:
- **Infrastructure Faults**: Terminating a Kubernetes pod, bringing down a node, filling up disk space, or causing CPU/Memory spikes.
- **Application Faults**: Inducing thread leaks, injecting latency into Java/Spring methods, or simulating application exceptions.

## How is it Achieved in MangleYaan?
1. **Target Identification**: The framework reads configuration (`my.json`) and queries **MaximGun** to determine the target Kubernetes cluster and workloads.
2. **Fault Injection**: MangleYaan uses the **VMware Mangle API** to execute the fault. For example, it sends an API request to Mangle instructing it to delete a specific microservice pod.
3. **State Validation**: While the fault is active, MangleYaan uses the **Kubernetes API** to monitor the state of the cluster (e.g., watching a new pod spin up).
4. **Behavior Assertion**: The framework uses **CSP APIs** (the product being tested) and UI automation to verify that the end-user experience remains uninterrupted or degrades gracefully.

## Expected Behavior
When a fault is injected (e.g., a critical service pod is deleted), the expected behaviors often include:
- **Resiliency**: The system should not crash entirely.
- **Self-Healing**: Kubernetes should automatically detect the missing pod and spin up a replacement (`ReplicaSet` behavior).
- **Graceful Degradation**: If the service is temporarily unavailable, dependent services should handle the timeout gracefully, perhaps by returning cached data or displaying a user-friendly error message, rather than timing out completely or throwing unhandled 500 exceptions.

By running these tests, MangleYaan ensures the system aligns with these resiliency expectations.
