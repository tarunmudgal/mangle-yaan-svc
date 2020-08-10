#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" common parameters used """

__author__ = "tarun mudgal"

from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, SSLError, Timeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError

# logger
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(lineno)d]: [%(funcName)s] %(message)s"
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
