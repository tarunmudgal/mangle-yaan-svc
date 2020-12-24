#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import urllib.parse

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.testlib import params
from src.testlib.selenium.locators.csp.base_page import BasePageLocators
from src.testlib.selenium.locators.csp.login_page import LoginPageLocators


# this Base class is serving basic attributes for every single page inherited from Page class
class BasePage:
    """
    Base class that keeps all common selenium APIs wrappers
    """

    browser_session = None

    def __init__(self, driver, base_url, timeout=30):
        self.driver = driver
        self.base_url = base_url
        self.timeout = timeout

        if BasePage.browser_session is None:
            self.go_to_url("/")
            self.wait_for_element(LoginPageLocators.TXT_LOGIN_TITLE, timeout=self.timeout)

    def wait_until_element_displays(timeout: int = None):
        """
        decorator to wait for an element before performing an action
        Returns:
            returns same value received from the function where this decorator is used
        """
        wd_timeout = timeout if timeout is not None else params.WEBDRIVER_DEFAULT_WAIT

        def _wait_to_display_wrapper(func):
            def _wait_to_display(self, *args, **kwargs):
                locator = args[0]
                try:
                    WebDriverWait(self.driver, wd_timeout).until(
                        EC.visibility_of_element_located(locator)
                    )
                except TimeoutException as fault:
                    mylog.exception(
                        "exception occurred as locator {} could not be found within {} seconds. Exception={}".format(
                            locator, params.WEBDRIVER_DEFAULT_WAIT, fault
                        )
                    )
                return func(self, *args, **kwargs)

            return _wait_to_display

        return _wait_to_display_wrapper

    def go_to_url(self, url="", is_abs_url=False):
        """
        go to a specific url from current url
        Args:
            url: relative url (relative to base url) e.g. "/csp/gateway/portal/#/consumer/billing/overview"
            is_abs_url: if set to True, url would be considered absolute

        Returns:
            None
        """
        if not is_abs_url:
            url = urllib.parse.urljoin(self.base_url, url)

        mylog.debug("going to url={}".format(url))
        self.driver.get(url)

    @wait_until_element_displays(timeout=60)
    def find_element(self, locator):
        """
        finds an element using locator
        Args:
            locator: locator to find a web-element

        Returns:
            web-element found using locator
        """
        try:
            return self.driver.find_element(*locator)
        except NoSuchElementException:
            return None

    def if_element_exists(self, locator):
        """
        checks if a web-element exists
        Args:
            locator: locator to find a web-element

        Returns:
            True if web-element exists else False
        """
        try:
            self.driver.find_element(*locator)
        except NoSuchElementException:
            return False

        return True

    def get_title(self):
        """ returns the title of the current page """
        return self.driver.title

    def get_url(self):
        """ returns the url of the current page """
        return self.driver.current_url

    def hover(self, locator):
        """
        moves mouse pointer on the element found using locator
        Args:
            locator: locator to find a web-element

        Returns:
            True if web-element found and mouse pointer moved over web-element else False
        """
        mylog.debug("hovering on locator={}".format(locator))
        element = self.find_element(locator)
        if element is None:
            mylog.error("could not find locator={}".format(locator))
            return False

        hover = ActionChains(self.driver).move_to_element(element)
        hover.perform()
        return True

    def send_keys(self, locator, value):
        """
        type text on the element found using locator
        Args:
            locator: locator to find a web-element

        Returns:
            True if web-element found and text written over web-element else False
        """
        mylog.debug("sending keys to locator={}".format(locator))
        web_element = self.find_element(locator)
        if web_element is None:
            mylog.error("could not find locator={}".format(locator))
            return False

        web_element.clear()
        web_element.send_keys(value)
        return True

    def click(self, locator):
        """
        click on the element found using locator
        Args:
            locator: locator to find a web-element

        Returns:
            True if web-element found and click succeeded over web-element else False
        """
        mylog.debug("clicking on locator={}".format(locator))
        web_element = self.find_element(locator)
        if web_element is None:
            mylog.error("could not find locator={}".format(locator))

        web_element.click()
        return True

    def wait_for_element(self, locator, timeout=10):
        """
        waits for a web-element to appear until timeout occurs
        Args:
            locator: locator to find a web-element
            timeout: timeout for web-element to appear

        Returns:
            True if web-element is found before timeout else False
        """
        mylog.debug("waiting for locator={} upto {} seconds".format(locator, timeout))
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            mylog.debug("element={} found".format(locator))
            return True
        except TimeoutException:
            # mylog.exception(
            #     "exception occurred as locator {} could not be found on url {} within {} seconds".format(
            #         locator, self.get_url(), timeout
            #     )
            # )
            mylog.error(
                "locator {} could not be found on url {} within {} seconds".format(
                    locator, self.get_url(), timeout
                )
            )

        return False

    def wait_for_spinner_to_disappear(
        self,
        spinner_locator=BasePageLocators.SPIN_LOGIN,
        timeout_to_appear=60,
        timeout_to_disappear=600,
    ):
        """
        waits for spinner to appear and once it's found, waits for spinner to disappear
        Args:
            spinner_locator: locator for the spinner
            timeout_to_appear: timeout for spinner to appear
            timeout_to_disappear: timeout for spinner to disappear

        Returns:
            True if spinner appeared first and disappeared after some time else False
        """
        mylog.debug("waiting for spinner to appear upto {} seconds".format(timeout_to_appear))

        spinner_found = False
        try:
            WebDriverWait(self.driver, timeout_to_appear).until(
                EC.visibility_of_element_located(spinner_locator)
            )
            mylog.debug("spinner found on url {}".format(self.get_url()))
            spinner_found = True
        except TimeoutException:
            # mylog.exception(
            #     "exception occurred as spinner {} could not be appeared on url {} within {} seconds".format(
            #         spinner_locator, self.get_url(), timeout_to_appear
            #     )
            # )
            mylog.error(
                "spinner {} could not be appeared on url {} within {} seconds".format(
                    spinner_locator, self.get_url(), timeout_to_disappear
                )
            )

        if spinner_found:
            mylog.debug(
                "waiting for spinner to disapper on url {} upto {} seconds".format(
                    self.get_url(), timeout_to_disappear
                )
            )
            try:
                WebDriverWait(self.driver, timeout_to_disappear).until(
                    EC.invisibility_of_element_located(spinner_locator)
                )
                mylog.debug("spinner disappeared from url {}".format(self.get_url()))

                return True

            except TimeoutException:
                # mylog.exception(
                #     "exception occurred as spinner {} could not be disappeared on url {} within {} seconds".format(
                #         spinner_locator, self.get_url(), timeout_to_disappear
                #     )
                # )
                mylog.error(
                    "spinner {} could not be disappeared on url {} within {} seconds".format(
                        spinner_locator, self.get_url(), timeout_to_disappear
                    )
                )

        return False
