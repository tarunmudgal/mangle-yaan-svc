#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = 'tarun mudgal'

# logger
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"
CONSOLE_LOG_LEVEL = "DEBUG"

# K8S
K8S_CLIENT = None
K8S_NAMESPACE = None
K8S_ENV_NAME = None

# Faults
FAULTY_SVC_ENV_NAME = "gameday"
FAULTY_SVC_NAMES_SET = set()
