#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "Y V Subba Reddy"

import pytest
import builtins

from test_runner import create_csp_client
from lib.csp import resources as csp_resources
from src.testlib.selenium.pages.csp.login_page import LoginPage
from src.testlib.selenium.pages.csp.iam_active_users_page import ActiveUsersPage
from src.testlib.selenium.pages.csp.iam_groups_page import GroupsPage
from src.testlib.selenium.pages.csp.iam_invitations_page import InvitationsPage
from src.testlib.selenium.pages.csp.iam_oauth_app_page import OauthAppsPage
from src.testlib.selenium.pages.csp.bs_overview_page import OverviewPage
from src.testlib.selenium.pages.csp.bs_payments_page import PaymentsPage
from src.testlib.selenium.pages.csp.bs_subscriptions_page import SubscriptionsPage
from src.testlib.selenium.pages.csp.bs_promotional_credits_page import PromotionalCreditsPage
from src.testlib.selenium.pages.csp.bs_invoices_page import InvoicesPage


USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"
PO_ORG_ID = "1c6f6c98-28bd-47b4-83f6-cad067495fce"
FF_CONFIG_CACHE_UPDATE_INTERVAL = 400


@pytest.mark.usefixtures(
    "update_csp_access_token", "block_commerce_endpoints_using_gateway_api", "init_chrome_driver",
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

        mylog.debug("Validating Active users page")
        active_users_page = ActiveUsersPage(self.driver, timeout=60)
        active_users_page.goto_active_users()

        mylog.debug("Validating Groups page")
        groups_page = GroupsPage(self.driver, timeout=60)
        groups_page.goto_groups_page()

        mylog.debug("Validating Pending Invitations Page")
        invitations_page = InvitationsPage(self.driver, timeout=60)
        invitations_page.goto_invitations_page()

        mylog.debug("Validating oAuth Apps Page")
        oauth_app_page = OauthAppsPage(self.driver, timeout=60)
        oauth_app_page.goto_oauth_app_page

        mylog.debug("Validating Billing and Subscription Overview Page")
        overview_page = OverviewPage(self.driver, timeout=60)
        overview_page.goto_overview_page()

        mylog.debug("Validating Manage Payments Method Page")
        payments_page = PaymentsPage(self.driver, timeout=60)
        payments_page.goto_payments_page()

        mylog.debug("Validating Subscription Page")
        sub_page = SubscriptionsPage(self.driver, timeout=60)
        sub_page.goto_subscriptions_page()

        mylog.debug("Validating Promotional Credits Page")
        credits_page = PromotionalCreditsPage(self.driver, timeout=60)
        credits_page.goto_promotional_credits_page()

        mylog.debug("Validating Invoice and Statements Page")
        invoice_page = InvoicesPage(self.driver, timeout=60)
        invoice_page.goto_invoices_page()

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))
