#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

# selenium grid
SELENIUM_GRID_HOST = "selenium-mangle-yaan.svc-stage.eng.vmware.com"
SELENIUM_GRID_PORT = "31001"
SELENIUM_GRID_CONSOLE_URI = "/grid/console"
SELENIUM_HUB_URI = "/wd/hub"

# WebDriver params
WEBDRIVER_DEFAULT_WAIT = 120

# CSP error code files
CSP_MODULE_CODE_FILE = "src/testlib/csp/errors/module_code.json"
CSP_MODULE_SERVICE_ERROR_CODE_FILES_MAP = {
    "250": "src/testlib/csp/errors/csp_common_errors.json",
    "330": "src/testlib/csp/errors/am_errors.json",
    "340": "src/testlib/csp/errors/am_idp_errors.json",
}


# csp urls
# CSP_BASE_URL = ""
