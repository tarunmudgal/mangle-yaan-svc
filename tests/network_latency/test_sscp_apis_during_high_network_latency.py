#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
from flaky import flaky

DEPLOYMENTS_COULD_NOT_BE_SCALED = False
DEPLOYMENT_NAMES_TO_BE_SCALED = ["csp-commerce"]
NEW_REPLICA_COUNT = 1


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.skipif(
    DEPLOYMENTS_COULD_NOT_BE_SCALED,
    reason="all deployments could not be scaled to {} replicas".format(NEW_REPLICA_COUNT),
)
@pytest.mark.usefixtures("inject_k8s_app_fault_spring_service_latency_for_class")
class TestSSCPAPIsWithHighNetworkLatency:
    SERVICE_LATENCY = 15000
    SERVICE_METHOD_VERB = "GET"
    SERVICE_URI = "/estimated-charges"
    CONTAINER_NAME = "csp-commerce"
    POD_LABELS = "app=csp-commerce"
    RANDOM_INJECTION = False
    JAVA_HOME_PATH = "/opt/jre"
    PORT = 9091

    def test_sscp_api1(self):
        mylog.info("dummy test 1")
        breakpoint()

    def test_sscp_api2(self):
        mylog.info("dummy test 2")
        assert 1 == 1

    # @pytest.mark.skipif(
    #     DEPLOYMENTS_COULD_NOT_BE_SCALED,
    #     reason="deployments could not be scaled to {} replicas".format(NEW_REPLICA_COUNT),
    # )
    # def test_csp_login_logout_when_minimal_services_are_up(self):
    #     loginpage = LoginPage(self.driver, timeout=60)
    #
    #     login_status = loginpage.do_login(
    #         TestCSPLoginLogoutWorkflow.USER, TestCSPLoginLogoutWorkflow.PASSWORD
    #     )
    #     assert login_status, "user {} could not login to CSP portal".format(
    #         TestCSPLoginLogoutWorkflow.USER
    #     )
    #     mylog.debug(
    #         "user {} logged-in to CSP portal successfully".format(TestCSPLoginLogoutWorkflow.USER)
    #     )
    #
    #     logout_status = loginpage.do_logout()
    #     assert logout_status, "user {} could not logout from CSP portal".format(
    #         TestCSPLoginLogoutWorkflow.USER
    #     )
    #     mylog.debug(
    #         "user {} logged-out from CSP portal successfully".format(
    #             TestCSPLoginLogoutWorkflow.USER
    #         )
    #     )
