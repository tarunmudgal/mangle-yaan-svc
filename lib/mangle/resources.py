#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" all api resources (endpoints) hosted by mangle """

__author__ = "tarun mudgal"

from collections import OrderedDict

# mangle API prefix
API_PREFIX = "/mangle-services"

# dict for INFRASTRUCTURE fault resources
INFRA_FAULTS = OrderedDict()
INFRA_FAULTS["CPU"] = "/rest/api/v1/faults/cpu"
INFRA_FAULTS["MEMORY"] = "/rest/api/v1/faults/memory"
INFRA_FAULTS["DISK_IO"] = "/rest/api/v1/faults/diskIO"
INFRA_FAULTS["KILL_PROCESS"] = "/rest/api/v1/faults/kill-process"
INFRA_FAULTS["FILE_HANDLER_LEAK"] = "/rest/api/v1/faults/filehandler-leak"
INFRA_FAULTS["DISK_SPACE"] = "/rest/api/v1/faults/disk-space"
INFRA_FAULTS["KERNEL_PANIC"] = "/rest/api/v1/faults/kernel-panic"
INFRA_FAULTS["K8S_DELETE_RESOURCE"] = "/rest/api/v1/faults/k8s/delete-resource"
INFRA_FAULTS["K8S_RESOURCE_NOT_READY"] = "/rest/api/v1/faults/k8s/resource-not-ready"
INFRA_FAULTS["K8S_RESOURCE_DELETE"] = "/rest/api/v1/faults/k8s/delete-resource"
INFRA_FAULTS["K8S_SERVICE_UNAVAILABLE"] = "/rest/api/v1/faults/k8s/service-unavailable"

# dict for APPLICATION fault resources
APP_FAULTS = OrderedDict()
APP_FAULTS["CPU"] = "/rest/api/v1/faults/cpu"
APP_FAULTS["MEMORY"] = "/rest/api/v1/faults/memory"
APP_FAULTS["FILE_HANDLER_LEAK"] = "/rest/api/v1/faults/filehandler-leak"
APP_FAULTS["THREAD_LEAK"] = "/rest/api/v1/faults/thread-leak"
APP_FAULTS["JAVA_METHOD_LATENCY"] = "/rest/api/v1/faults/java-method-latency"
APP_FAULTS["SPRING_SERVICE_LATENCY"] = "/rest/api/v1/faults/spring-service-latency"
APP_FAULTS["SPRING_SERVICE_EXCEPTION"] = "/rest/api/v1/faults/spring-service-exception"
APP_FAULTS["SIMULATE_JAVA_EXCEPTION"] = "/rest/api/v1/faults/simulate-java-exception"
APP_FAULTS["KILL_JVM"] = "/rest/api/v1/faults/kill-jvm"

OTHER_FAULTS = OrderedDict()
OTHER_FAULTS["REMEDIATION"] = "/rest/api/v1/faults"

# all faults map
FAULTS = OrderedDict()
FAULTS["INFRA"] = INFRA_FAULTS
FAULTS["APP"] = APP_FAULTS
FAULTS["OTHER"] = OTHER_FAULTS

# mangle endpoint-controller resources
EP_CTRLR = OrderedDict()
EP_CTRLR["ENDPOINTS"] = "/rest/api/v1/endpoints"
EP_CTRLR["CREDENTIALS"] = "/rest/api/v1/endpoints/credentials"
EP_CTRLR["K8S_CREDENTIALS"] = "/rest/api/v1/endpoints/credentials/k8s"
EP_CTRLR["TEST_CONNECTION"] = "/rest/api/v1/endpoints/testConnection"
EP_CTRLR["TEST_ENDPOINT"] = "/rest/api/v1/endpoints/testEndpoint"

# mangle task-controller resources
TASK_CTRLR = OrderedDict()
TASK_CTRLR["TASKS"] = "/rest/api/v1/tasks"
TASK_CTRLR["TASKS_CLEANUP"] = "/rest/api/v1/tasks/clean-up"
TASK_CTRLR["TASK"] = "/rest/api/v1/tasks/{taskId}"
