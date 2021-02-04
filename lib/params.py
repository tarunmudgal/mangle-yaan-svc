#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" common parameters used """

__author__ = "tarun mudgal"

import os
from collections import OrderedDict

from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, SSLError, Timeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError

# test_runner
LOG_DIR = ""
CONF_DIR = ""
TESTSUITES_DIR = ""
SRC_DIR = ""
TESTLIB_DIR = ""
ALLURE_LOG_DIR = ""

# logger
LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d]: [%(funcName)s] %(message)s"
)
LOG_DATE_FORMAT = "%d-%m-%Y %I:%M:%S %p"

CONSOLE_LOG_LEVEL = "DEBUG"
FILE_LOG_FILENAME = "test_runner.log"
FILE_LOG_LEVEL = "DEBUG"
FILE_LOG_MAX_BYTES = 1_000_000
FILE_LOG_BACKUP_COUNT = 5

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


# mangle_client
MCLIENT_MAX_RETRIES = 3
MCLIENT_STATUS_FORCELIST = [429, 500, 502, 503, 504]
MCLIENT_METHOD_WHITELIST = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE"]
MCLIENT_BACKOFF_FACTOR = 1

# Mangle task staus
MANGLE_TASK_STATUS = OrderedDict()
MANGLE_TASK_STATUS["NOT_STARTED"] = "NOT STARTED"
MANGLE_TASK_STATUS["IN_PROGRESS"] = "IN_PROGRESS"
MANGLE_TASK_STATUS["COMPLETED"] = "COMPLETED"
MANGLE_TASK_STATUS["FAILED"] = "FAILED"


# maximgun_client
MGCLIENT_MAX_RETRIES = 3
MGCLIENT_STATUS_FORCELIST = [429, 500, 502, 503, 504]
MGCLIENT_METHOD_WHITELIST = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PUT", "HEAD", "TRACE"]
MGCLIENT_BACKOFF_FACTOR = 1

# Maxim-Gun task staus
MG_TASK_STATUS = OrderedDict()
MG_TASK_STATUS["STARTED"] = "Started"
MG_TASK_STATUS["IN_PROGRESS"] = "Running"
MG_TASK_STATUS["COMPLETED"] = "Completed"
MG_TASK_STATUS["FAILED"] = "Failed"
MG_TASK_STATUS["CANCELLED"] = "Cancelled"

# Maxim-Gun datetime format
MG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


# MangleYaan aggregated result to be pushed to maxim_gun.run_test.baseline_result
MANGLEYAAN_AGGREGATED_RESULT = OrderedDict()
MANGLEYAAN_AGGREGATED_RESULT["PASS"] = "PASS"
MANGLEYAAN_AGGREGATED_RESULT["FAIL"] = "FAIL"
MANGLEYAAN_AGGREGATED_RESULT["PARTIAL_PASS"] = "PARTIALLY_PASS"

# MangleYaan aggregated result thresholds %
MANGLEYAAN_PASS_THRESHOLD = 90
MANGLEYAAN_PARTIALLY_PASS_THRESHOLD = 75

# MangleYaan task update interval (in seconds)
MANGLEYAAN_TASK_UPDATE_INTERVAL = 90
