#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

import json

from src.testlib import params
from typing import Dict

__author__ = "tarun mudgal"

CSP_MODULE_CODES = None
CSP_MODULE_SERVICE_ERROR_CODES_MAP: Dict[str, Dict] = None


def get_csp_module_error_code_info(module_code: str) -> dict:
    global CSP_MODULE_CODES
    if CSP_MODULE_CODES is None:
        with open(params.CSP_MODULE_CODE_FILE) as json_file:
            CSP_MODULE_CODES = json.load(json_file)
    return CSP_MODULE_CODES.get(module_code, None)


def get_csp_service_error_code_info(module_code: int, service_code: str) -> dict:
    global CSP_MODULE_SERVICE_ERROR_CODES_MAP
    if CSP_MODULE_SERVICE_ERROR_CODES_MAP is None:
        CSP_MODULE_SERVICE_ERROR_CODES_MAP = {}
        for mod_code, error_code_file in params.CSP_MODULE_SERVICE_ERROR_CODE_FILES_MAP.items():
            CSP_MODULE_SERVICE_ERROR_CODES_MAP[mod_code] = {}
            with open(error_code_file) as json_file:
                CSP_MODULE_SERVICE_ERROR_CODES_MAP[mod_code].update(json.load(json_file))
    return CSP_MODULE_SERVICE_ERROR_CODES_MAP[module_code].get(service_code, None)


def get_module_service_error_types(csp_error_code: str) -> list:
    if not csp_error_code:
        mylog.error("invalid csp_error_code found. csp_error_code={}".format(csp_error_code))
        return []

    csp_error_codes = csp_error_code.split("-")

    module_service_error_types = []
    for mod_svc_code in csp_error_codes:
        module_error_code, svc_error_code = mod_svc_code.split(".")
        module_error_type = get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = get_csp_service_error_code_info(module_error_code, svc_error_code)
        module_service_error_types.append((module_error_type, svc_error_type))

    return module_service_error_types
