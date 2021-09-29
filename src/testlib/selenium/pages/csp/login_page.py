#!/usr/bin/env python
# -- coding: utf-8 --
""" module description """

__author__ = "tarun mudgal"

from src.testlib.selenium.locators.csp import login_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.base_url = "https://" + myconfig.get("csp").get(csp_env).get("host")
        self.locators = login_page.LoginPageLocators
        super().__init__(driver, self.base_url, timeout=timeout)

    def goto_login_page(self):
        login_page_locators = [self.locators.TXT_LOGIN_TITLE, self.locators.TXT_PASSWORD_FORM]
        if not self.if_any_element_exists(login_page_locators):
            mylog.info(
                "locators={} not found. redirecting to login page".format(login_page_locators)
            )
            self.go_to_url("/")
            self.wait_until_any_element_exists(login_page_locators, timeout=self.timeout)
        mylog.info("reached on login page")

    def do_login(self, email, password):
        self.goto_login_page()

        if self.if_element_exists(self.locators.LNK_SIGN_IN_USING_ANOTHER_ACCT):
            self.click(self.locators.LNK_SIGN_IN_USING_ANOTHER_ACCT)
        elif self.if_element_exists(self.locators.BTN_BACK_TO_LOGIN):
            self.click(self.locators.BTN_BACK_TO_LOGIN)

        if self.if_element_exists(self.locators.TB_EMAIL):
            self.send_keys(self.locators.TB_EMAIL, email)
            assert self.if_element_exists(
                self.locators.BTN_NEXT
            ), "could not find NEXT button locator={}".format(self.locators.BTN_NEXT)
            self.click(self.locators.BTN_NEXT)

        if self.if_element_exists(self.locators.TB_PASSWORD):
            self.send_keys(self.locators.TB_PASSWORD, password)
            assert self.if_element_exists(
                self.locators.BTN_SIGN_IN
            ), "could not find SIGN IN button locator={}".format(self.locators.BTN_SIGN_IN)
            self.click(self.locators.BTN_SIGN_IN)

        self.wait_for_spinner_to_disappear(timeout_to_appear=60, timeout_to_disappear=120)

        logged_in = self.wait_for_element(self.locators.TXT_HOME_TITLE, timeout=300)

        return logged_in

    def do_login_with_minimal_services(self, email, password):
        self.goto_login_page()

        assert self.if_element_exists(
            self.locators.TB_EMAIL
        ), "could not find email text box locator={}".format(self.locators.TB_EMAIL)
        self.send_keys(self.locators.TB_EMAIL, email)

        assert self.if_element_exists(
            self.locators.BTN_NEXT
        ), "could not find NEXT button locator={}".format(self.locators.BTN_NEXT)
        self.click(self.locators.BTN_NEXT)

        self.wait_for_element(self.locators.TB_PASSWORD)
        assert self.if_element_exists(
            self.locators.TB_PASSWORD
        ), "could not find password text box locator={}".format(self.locators.TB_PASSWORD)
        self.send_keys(self.locators.TB_PASSWORD, password)

        assert self.if_element_exists(
            self.locators.BTN_SIGN_IN
        ), "could not find SIGN IN button locator={}".format(self.locators.BTN_SIGN_IN)
        self.click(self.locators.BTN_SIGN_IN)

        self.wait_for_spinner_to_disappear(timeout_to_appear=60, timeout_to_disappear=600)

        logged_in = self.wait_for_element(self.locators.TXT_HOME_TITLE, timeout=600)

        return logged_in

    def do_logout(self):
        assert self.if_element_exists(
            self.locators.BTN_USER_MENU
        ), "could not find user menu button locator={}".format(self.locators.TB_EMAIL)

        self.click(self.locators.BTN_USER_MENU)
        self.click(self.locators.BTN_SIGN_OUT)

        # logged_out = self.wait_for_element(self.locators.TXT_LOGOUT_MSG, timeout=180)
        logged_out_status, found_element = self.wait_until_any_element_exists([self.locators.TXT_LOGOUT_MSG,
                                                            self.locators.TXT_LOGIN_TITLE], timeout=180)

        return logged_out_status

    def do_logout_with_minimal_services(self):
        assert self.if_element_exists(
            self.locators.BTN_USER_MENU
        ), "could not find user menu button locator={}".format(self.locators.TB_EMAIL)

        self.click(self.locators.BTN_USER_MENU)
        self.click(self.locators.BTN_SIGN_OUT)

        logged_out = self.wait_for_element(self.locators.TXT_LOGOUT_MSG, timeout=180)

        return logged_out
