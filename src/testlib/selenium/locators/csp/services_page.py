#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from selenium.webdriver.common.by import By

# naming convention for locator names
# <type>_<name>
# types: TB=Text Box; BTN=Button; DD=Drop Down; TXT=Text;


class ServicesPageLocators:
    BTN_ERROR_OCCURED = (By.CLASS_NAME, "btn btn-primary")
