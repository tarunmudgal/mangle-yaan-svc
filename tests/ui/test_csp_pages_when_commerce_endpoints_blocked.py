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
PO_ORG_ID = "1c6f6c98-28bd-47b4-83f6-cad067495fce"
FF_CONFIG_CACHE_UPDATE_INTERVAL = 120


# @pytest.mark.usefixtures("update_csp_access_token","test_csp_ui_when_kong_gateway_commerce_api_is_blocked","init_chrome_driver")
@pytest.mark.usefixtures("init_chrome_driver")
class TestCSPPagesWhenCommerceEndpointsBlocked:
    expected_res_code = 200

    def test_iam_commerce_pages_when_commerce_endpoints_blocked(self):
        # pass
        loginpage = LoginPage(self.driver, timeout=60)
        breakpoint()

        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

    



    


        


