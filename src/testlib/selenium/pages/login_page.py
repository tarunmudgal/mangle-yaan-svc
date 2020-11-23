#!/usr/bin/env python
# -- coding: utf-8 --
""" module description """

__author__ = "tarun mudgal"

from src.testlib.selenium.locators import login_page
from src.testlib.selenium.pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, driver, base_url, timeout=30):
        self.locators = login_page.LoginPageLocators
        super().__init__(driver, base_url, timeout=timeout)

    def goto_login_page(self):
        login_url = "https://" + myconfig.get("csp").get("host")
        if not self.driver.session_id:
            mylog.info("no session found for driver. opening a new browser window...")
            self.open()
            mylog.info("waiting for locator={}".format(self.locators.TXT_WELCOME_TITLE))
            self.wait_for_element(self.locators.TXT_WELCOME_TITLE)
        if not self.find_element(self.locators.TXT_WELCOME_TITLE):
            mylog.info(
                "locator={} not found. redirecting to login page".format(
                    self.locators.TXT_WELCOME_TITLE
                )
            )
            self.open()
            mylog.info("waiting for locator={}".format(self.locators.TXT_WELCOME_TITLE))
            self.wait_for_element(self.locators.TXT_WELCOME_TITLE)
        mylog.info("reached on to login page")

    def do_login(self, email, password):
        self.goto_login_page()
        if not self.find_element(self.locators.TB_EMAIL):
            mylog.error("could not find locator={}".format(self.locators.TB_EMAIL))
        self.find_element(self.locators.TB_EMAIL).send_keys(email)
        if not self.find_element(self.locators.BTN_NEXT):
            mylog.error("could not find locator={}".format(self.locators.BTN_NEXT))
        self.find_element(self.locators.BTN_NEXT).click()
        self.wait_for_element(self.locators.TB_PASSWORD)
        if not self.find_element(self.locators.TB_PASSWORD):
            mylog.error("could not find locator={}".format(self.locators.TB_PASSWORD))
        self.find_element(self.locators.TB_PASSWORD).send_keys(password)
        if not self.find_element(self.locators.BTN_SIGN_IN):
            mylog.error("could not find locator={}".format(self.locators.BTN_SIGN_IN))
        self.find_element(self.locators.BTN_SIGN_IN).click()

        mylog.info("waiting for locator={}".format(self.locators.TXT_HOME_TITLE))
        self.wait_for_element(self.locators.TXT_HOME_TITLE)
