#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" common parameters used """

__author__ = "tarun mudgal"

from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, SSLError, Timeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError
from collections import OrderedDict

# logger
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"

# rest_client
HTTP_RETRIABLE_ERRORS = (
    ConnectionError,
    ConnectTimeout,
    ConnectTimeoutError,
    ReadTimeout,
    SSLError,
    Timeout,
)

# Mangle task staus
MANGLE_TASK_STATUS = OrderedDict()
MANGLE_TASK_STATUS["NOT_STARTED"] = "NOT STARTED"
MANGLE_TASK_STATUS["IN_PROGRESS"] = "IN_PROGRESS"
MANGLE_TASK_STATUS["COMPLETED"] = "COMPLETED"
MANGLE_TASK_STATUS["FAILED"] = "FAILED"

# MangleYaan Task Error Status
MANGLEYAAN_TASK_STATUS = OrderedDict()
MANGLEYAAN_TASK_STATUS["NOT_FETCHED"] = ""