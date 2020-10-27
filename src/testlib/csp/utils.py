#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

from src.testlib import params
import json

__author__ = 'tarun mudgal'

CSP_MODULE_CODES = None
CSP_SERVICE_ERROR_CODES = None

def get_csp_module_error_code_info(module_code: int) -> dict:
    global CSP_MODULE_CODES
    if CSP_MODULE_CODES is None:
        with open(params.CSP_MODULE_CODE_FILE) as json_file:
            CSP_MODULE_CODES = json.load(json_file)
    return CSP_MODULE_CODES.get(module_code, None)

def get_csp_service_error_code_info(service_code: int) -> dict:
    global CSP_SERVICE_ERROR_CODES
    if CSP_SERVICE_ERROR_CODES is None:
        CSP_SERVICE_ERROR_CODES = {}
        for error_code_file in params.CSP_SERVICE_ERROR_CODE_FILES:
            with open(error_code_file) as json_file:
                CSP_SERVICE_ERROR_CODES.update(json.load(json_file))
    return CSP_SERVICE_ERROR_CODES.get(service_code, None)
