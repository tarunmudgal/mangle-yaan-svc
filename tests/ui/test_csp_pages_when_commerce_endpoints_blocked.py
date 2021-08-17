#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "Y V Subba Reddy"

from src.testlib.selenium.locators.csp import iam_active_users_page
import pytest
import builtins

from test_runner import create_csp_client
from lib.csp import resources as csp_resources
from src.testlib.selenium.pages.csp.login_page import LoginPage
from src.testlib.selenium.pages.csp.iam_active_users_page import ActiveUsersPage
from src.testlib.selenium.pages.csp.bs_subscriptions_page import SubscriptionsPage


USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"
PO_ORG_ID = "1c6f6c98-28bd-47b4-83f6-cad067495fce"
FF_CONFIG_CACHE_UPDATE_INTERVAL = 300


@pytest.mark.usefixtures(
    "update_csp_access_token",
    "block_commerce_endpoints_using_gateway_api",
    "init_chrome_driver",
)
class TestCSPPagesWhenCommerceEndpointsBlocked:

    #
    # def test_get_org_details_when_commerce_api_blocked(PO_ORG_ID):
    #     expected_status_code = 503
    #
    #     api_resource = csp_resources.COMMERCE.get("ORG_DETAILS").format(
    #         orgId=PO_ORG_ID
    #     )
    #
    #     resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)
    #
    #     # verify csp api returns expected_status_code
    #     assert (
    #             resp.status_code == expected_status_code
    #     ), "AM service did not return expected status_code={}".format(expected_status_code)

    def test_iam_commerce_pages_when_commerce_endpoints_blocked(self):
        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))
        iam_page = ActiveUsersPage(self.driver, timeout=60)

        active_users = iam_page.goto_active_users()
        assert active_users == "Active Users", "Active users page is not working as expected"
        mylog.debug("Active users Page working as expected.")

        sub_page = SubscriptionsPage(self.driver, timeout=60)
        subscription_status = sub_page.goto_subscriptions_page()
        assert (
            subscription_status
            == "VMware Cloud commerce Services is undergoing scheduled maintenance right now."
        ), "scbscription page not working as expected"
        mylog.debug("Subscription Page working as expected.")

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))
