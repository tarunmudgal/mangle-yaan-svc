#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

# logger
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"
CONSOLE_LOG_LEVEL = "DEBUG"

# K8S
K8S_CLIENT = None
K8S_NAMESPACE = None
K8S_ENV_NAME = None

# Faults
FAULTY_SVC_ENV_NAME = "gameday"
FAULTY_SVC_NAMES_SET = set()

# external service unavailability - network policy
NETWORK_POLICY_MAP = {
    "dev": {
        "commerce-deny-external-egress-on-dev": {
            "filename": "dev_env_egress_commerce_service.yaml",
            "description": "this network policy blocks egress traffic from "
            "csp-commerce and csp-iam-vmwid service pods in "
            "csp-app-dev namespace",
        },
        "am-deny-external-egress-on-dev": {
            "filename": "dev_env_egress_am_service.yaml",
            "description": "this network policy blocks egress traffic from "
            "csp-account-management-mvc service pods in "
            "csp-app-dev namespace",
        },
    },
    "preview": {},
}
