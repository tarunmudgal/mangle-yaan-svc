#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from selenium.webdriver.common.by import By

# naming convention for locator names
# <type>_<name>
# types: TB=Text Box; BTN=Button; DD=Drop Down; TXT=Text;


class LoginPageLocators:
    TB_EMAIL = (By.ID, "discovery_username")
    BTN_NEXT = (By.ID, "next-btn")
    TB_PASSWORD = (By.ID, "password")
    BTN_SIGN_IN = (By.XPATH, "//button[contains(text(),'SIGN IN')]")
    TXT_LOGIN_TITLE = (By.ID, "csp-welcome-title")
    TXT_HOME_TITLE = (By.CLASS_NAME, "title")
    BTN_USER_MENU = (By.ID, "btn-csp-user")
    BTN_SIGN_OUT = (By.ID, "csp-sign-out-btn")
    TXT_LOGOUT_MSG = (By.CLASS_NAME, "logout-message")
    LNK_SIGN_IN_USING_ANOTHER_ACCT = (By.LINK_TEXT, "Sign in using another account")
