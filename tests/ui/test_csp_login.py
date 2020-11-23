#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest

from src.testlib.selenium.pages.login_page import LoginPage


@pytest.mark.usefixtures("init_chrome_driver")
class TestCSPLogin:
    def test_csp_login(self):
        breakpoint()
        loginpage = LoginPage(self.driver, "https://console-preview.cloud.vmware.com")
        loginpage.do_login("lhruser3usd@yahoo.com", "Test@123")
