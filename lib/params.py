#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" common parameters used """

__author__ = "tarun mudgal"

from collections import OrderedDict

from requests.exceptions import (ConnectionError, ConnectTimeout,
                                 ReadTimeout, SSLError, Timeout)
from requests.packages.urllib3.exceptions import ConnectTimeoutError

# logger
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
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

# csp_client
CCLIENT_MAX_RETRIES = 3
CCLIENT_STATUS_FORCELIST = [429, 500, 502, 503, 504]
CCLIENT_METHOD_WHITELIST = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE"]
CCLIENT_BACKOFF_FACTOR = 1

# csp_client
MCLIENT_MAX_RETRIES = 3
MCLIENT_STATUS_FORCELIST = [429, 500, 502, 503, 504]
MCLIENT_METHOD_WHITELIST = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE"]
MCLIENT_BACKOFF_FACTOR = 1

# maximgun_client
MGCLIENT_MAX_RETRIES = 3
MGCLIENT_STATUS_FORCELIST = [429, 500, 502, 503, 504]
MGCLIENT_METHOD_WHITELIST = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE"]
MGCLIENT_BACKOFF_FACTOR = 1

# Mangle task staus
MANGLE_TASK_STATUS = OrderedDict()
MANGLE_TASK_STATUS["NOT_STARTED"] = "NOT STARTED"
MANGLE_TASK_STATUS["IN_PROGRESS"] = "IN_PROGRESS"
MANGLE_TASK_STATUS["COMPLETED"] = "COMPLETED"
MANGLE_TASK_STATUS["FAILED"] = "FAILED"

# Maxim-Gun task staus
MG_TASK_STATUS = OrderedDict()
MG_TASK_STATUS["STARTED"] = "Test started"
MG_TASK_STATUS["IN_PROGRESS"] = "Test running"
MG_TASK_STATUS["COMPLETED"] = "Done"
MG_TASK_STATUS["FAILED"] = "Test Failed"
MG_TASK_STATUS["CANCELLED"] = "Test Cancelled"

# MangleYaan Task Error Status
MANGLEYAAN_TASK_STATUS = OrderedDict()
MANGLEYAAN_TASK_STATUS["NOT_FETCHED"] = ""
