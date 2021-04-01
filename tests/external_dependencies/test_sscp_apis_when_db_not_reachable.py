#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
import requests
from flaky import flaky

from lib.csp import resources
from src.testlib.csp import utils as csp_utils
from src.testlib.pytest import utils as pytest_utils

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_commerce_service.yaml"]


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class",
    LIST_NETWORK_POLICY_FILENAMES,
    indirect=True,
)
class TestSSCPAPIsWhenDBServiceNotReachable:
    """
    test cases for CSP APIs when GAZ service calls are blocked
    """

    @pytest.mark.dependency()
    def test_get_org_sellers_v3_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_SELLERS_CREATED_IN_ORGANIZATION_V3").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_get_org_billing_accounts_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_ORG_BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_get_all_sellers_details_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_ALL_SELLERS_DETAILS")

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_get_orders_for_given_seller_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_ORDERS_FOR_GIVEN_SELLER").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_get_billing_accounts_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_ORG_BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_get_default_billing_accounts_api_when_db_service_calls_are_blocked(
            self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = [500, 504]

        # make csp api call

        api_resource = resources.COMMERCE.get("GET_ORG_BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
                resp.status_code in expected_http_code
        ), "Database service didn't return expected status_code={}".format(expected_http_code)