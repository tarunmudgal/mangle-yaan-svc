#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from selenium.webdriver.common.by import By

# naming convention for locator names
# <type>_<name>
# types: TB=Text Box; BTN=Button; DD=Drop Down; TXT=Text; SPIN=Spinner


class BasePageLocators:
    SPIN_LOGIN = (By.CLASS_NAME, "spinner")
    BTN_ERROR_OCCURED = (By.XPATH, "//button[contains(text(),'Ok')]")
