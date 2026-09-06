# VMware Mangle API Reference

VMware Mangle is an open-source fault injection tool that is currently end-of-life ([Archive Link](https://github.com/vmware-archive/mangle)).
This document serves as a local reference for the specific Mangle APIs utilized by the **MangleYaan** framework to execute chaos experiments.

> **Note:** The base path for all endpoints is typically the Mangle host URL appended with `/mangle-services`.

## Authentication and Headers

The `MangleClient` (located in `lib/mangle/mangle_client.py`) utilizes Basic Authentication. When making a request, the username and password are base64 encoded and passed in the `Authorization` header.

**Standard Headers:**
```http
Authorization: Basic <base64(username:password)>
Content-Type: application/json
Accept: application/json
```

---

## Example Payload and API Call

Below is an example of injecting an infrastructure fault (e.g., K8S_DELETE_RESOURCE) using a REST client like `curl`.

### Request
```bash
curl -X POST "https://<mangle-host>/mangle-services/rest/api/v1/faults/k8s/delete-resource" \
  -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
  -H "Content-Type: application/json" \
  -d '{
    "endpointName": "my-k8s-cluster",
    "resourceLabels": {
      "app": "my-microservice"
    },
    "randomInjection": true,
    "faultName": "Delete Pod Fault",
    "schedule": {
      "timeInMilliseconds": 1600000000000
    }
  }'
```

### Response
```json
{
  "id": "task-uuid-1234-5678",
  "taskName": "Delete Pod Fault",
  "taskStatus": "IN_PROGRESS",
  "taskDescription": "Executing delete resource fault on K8s"
}
```

---

## 1. Infrastructure Faults (INFRA)

These endpoints are used to inject faults at the infrastructure layer (e.g., K8s nodes, resources, underlying hardware simulation).

| Fault Type                  | API Endpoint Path                              |
|-----------------------------|------------------------------------------------|
| **CPU**                     | `/rest/api/v1/faults/cpu`                      |
| **MEMORY**                  | `/rest/api/v1/faults/memory`                   |
| **DISK_IO**                 | `/rest/api/v1/faults/diskIO`                   |
| **KILL_PROCESS**            | `/rest/api/v1/faults/kill-process`             |
| **FILE_HANDLER_LEAK**       | `/rest/api/v1/faults/filehandler-leak`         |
| **DISK_SPACE**              | `/rest/api/v1/faults/disk-space`               |
| **KERNEL_PANIC**            | `/rest/api/v1/faults/kernel-panic`             |
| **K8S_DELETE_RESOURCE**     | `/rest/api/v1/faults/k8s/delete-resource`      |
| **K8S_RESOURCE_NOT_READY**  | `/rest/api/v1/faults/k8s/resource-not-ready`   |
| **K8S_RESOURCE_DELETE**     | `/rest/api/v1/faults/k8s/delete-resource`      |
| **K8S_SERVICE_UNAVAILABLE** | `/rest/api/v1/faults/k8s/service-unavailable`  |


## 2. Application Faults (APP)

These endpoints inject faults directly into application containers, typically JVM-based or Spring-based services.

| Fault Type                   | API Endpoint Path                               |
|------------------------------|-------------------------------------------------|
| **CPU**                      | `/rest/api/v1/faults/cpu`                       |
| **MEMORY**                   | `/rest/api/v1/faults/memory`                    |
| **FILE_HANDLER_LEAK**        | `/rest/api/v1/faults/filehandler-leak`          |
| **THREAD_LEAK**              | `/rest/api/v1/faults/thread-leak`               |
| **JAVA_METHOD_LATENCY**      | `/rest/api/v1/faults/java-method-latency`       |
| **SPRING_SERVICE_LATENCY**   | `/rest/api/v1/faults/spring-service-latency`    |
| **SPRING_SERVICE_EXCEPTION** | `/rest/api/v1/faults/spring-service-exception`  |
| **SIMULATE_JAVA_EXCEPTION**  | `/rest/api/v1/faults/simulate-java-exception`   |
| **KILL_JVM**                 | `/rest/api/v1/faults/kill-jvm`                  |


## 3. Other Faults & Remediation

Used generally for remediation and cleanup of faults.

| Action          | API Endpoint Path    |
|-----------------|----------------------|
| **REMEDIATION** | `/rest/api/v1/faults`|


## 4. Endpoint Controller

APIs used to configure and test target endpoints in Mangle before injecting faults.

| Resource               | API Endpoint Path                                |
|------------------------|--------------------------------------------------|
| **ENDPOINTS**          | `/rest/api/v1/endpoints`                         |
| **CREDENTIALS**        | `/rest/api/v1/endpoints/credentials`             |
| **K8S_CREDENTIALS**    | `/rest/api/v1/endpoints/credentials/k8s`         |
| **TEST_CONNECTION**    | `/rest/api/v1/endpoints/testConnection`          |
| **TEST_ENDPOINT**      | `/rest/api/v1/endpoints/testEndpoint`            |


## 5. Task Controller

APIs for retrieving information about executing or finished fault injection tasks.

| Resource          | API Endpoint Path                        |
|-------------------|------------------------------------------|
| **TASKS**         | `/rest/api/v1/tasks`                     |
| **TASKS_CLEANUP** | `/rest/api/v1/tasks/clean-up`            |
| **TASK**          | `/rest/api/v1/tasks/{taskId}`            |
