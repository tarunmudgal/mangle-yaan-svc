#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from selenium.webdriver.common.by import By

# naming convention for locator names
# <type>_<name>
# types: TB=Text Box; BTN=Button,


class LoginPageLocators:
    TB_EMAIL = (By.ID, "discovery_username")
    BTN_NEXT = (By.ID, "next-btn")
    TB_PASSWORD = (By.ID, "password")
    BTN_SIGN_IN = (By.CLASS_NAME, "btn btn-primary")
    TXT_WELCOME_TITLE = (By.ID, "csp-welcome-title")
    TXT_HOME_TITLE = (By.CLASS_NAME, "title")
