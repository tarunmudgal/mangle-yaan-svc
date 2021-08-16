#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "Y V Subba Reddy"

import pytest
import builtins

from test_runner import create_csp_client
from lib.csp import resources
from src.testlib.selenium.pages.csp.login_page import LoginPage


USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"


@pytest.mark.usefixtures("update_csp_access_token","test_csp_ui_when_kong_gateway_commerce_api_is_blocked","init_chrome_driver")
class TestBlockingKongGatewayApi:
    expected_res_code = 200

    def test_blocking_api(self):
        expected_status_code = 200

        assert expected_status_code == resp.status_code, "Kong gateway api is not blocked"

        

    def test_login_page():

        loginpage = LoginPage(self.driver, timeout=60)

        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))
        pass

    



    


        


