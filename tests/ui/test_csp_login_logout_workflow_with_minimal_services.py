#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
from flaky import flaky

from src.testlib.selenium.pages.csp.login_page import LoginPage


DEPLOYMENT_NAMES_TO_BE_SCALED = [
    "csp-audit-consumer",
    "csp-billing-mvc",
    "csp-billing-sdp",
    "csp-branding",
    "csp-commerce",
    "csp-commerce-aws-adapter",
    "csp-commerce-notifications",
    "csp-commerce-sap-adapter",
    "csp-customer-management",
    "csp-customer-support",
    "csp-data-aggregator",
    "csp-data-enrichment",
    "csp-data-mediator",
    "csp-email",
    "csp-federation",
    "csp-ff-service",
    "csp-fraud-management",
    "csp-iam-vmwid",
    "csp-identity-governance",
    "csp-lake-consumer",
    "csp-onboarding",
    "csp-operator-portal",
    "csp-post-office",
    "csp-promotional-info",
    "csp-resource-manager",
    "csp-rtc",
    "csp-usage-meter",
    "ns-event-service",
    "ns-inapp",
]

NEW_REPLICA_COUNT = 0
USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"
DEPLOYMENTS_COULD_NOT_BE_SCALED = False


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.usefixtures("scale_deployments_for_class", "init_chrome_driver")
class TestCSPLoginLogoutWorkflow:
    @pytest.mark.skipif(
        DEPLOYMENTS_COULD_NOT_BE_SCALED,
        reason="all deployments could not be scaled to {} replicas".format(NEW_REPLICA_COUNT),
    )
    def test_csp_login_logout_when_minimal_services_are_up(self):
        loginpage = LoginPage(self.driver, timeout=60)

        login_status = loginpage.do_login_with_minimal_services(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        logout_status = loginpage.do_logout_with_minimal_services()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))
