#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.testlib import params
from src.testlib.selenium.locators import login_page as login_page_locators


# this Base class is serving basic attributes for every single page inherited from Page class
class BasePage:
    browser_session = None

    def __init__(self, driver, base_url, timeout=30):
        self.driver = driver
        self.base_url = base_url
        self.timeout = timeout

        if BasePage.browser_session is None:
            self.open()
            self.wait_for_element(
                login_page_locators.LoginPageLocators.TXT_WELCOME_TITLE, timeout=120
            )

    def wait_if_element_not_displayed(func):
        def _wait_to_display(self, *args, **kwargs):
            locator = args[0]
            try:
                WebDriverWait(self.driver, params.WEBDRIVER_DEFAULT_WAIT).until(
                    lambda s: s.find_element(*locator).is_displayed()
                )
            except TimeoutException as fault:
                mylog.exception(
                    "exception occurred as locator {} could not be found within {} seconds. Exception={}".format(
                        locator, params.WEBDRIVER_DEFAULT_WAIT, fault
                    )
                )
            return func(self, *args, **kwargs)

        return _wait_to_display

    def open(self, url="", abs_url=False):
        if not abs_url:
            url = self.base_url + url
        self.driver.get(url)

    @wait_if_element_not_displayed
    def find_element(self, locator):
        return self.driver.find_element(*locator)

    def get_title(self):
        return self.driver.title

    def get_url(self):
        return self.driver.current_url

    def hover(self, *locator):
        element = self.find_element(*locator)
        hover = ActionChains(self.driver).move_to_element(element)
        hover.perform()

    def wait_for_element(self, locator, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda s: s.find_element(*locator).is_displayed()
            )
        except TimeoutException as fault:
            mylog.exception(
                "exception occurred as locator {} could not be found on url {} within {} seconds".format(
                    locator, self.get_url(), timeout
                )
            )
            self.driver.quit()

    def send_keys(self, locator, value):
        web_element = self.find_element(locator)
        if not web_element:
            mylog.error("could not find locator={}".format(locator))
        web_element.clear()
        web_element.send_keys(value)
