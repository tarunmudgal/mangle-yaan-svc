#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import pytest
import requests
from lib.csp import resources


@pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_am")
class TestCommerceDependencyOnAM:
    def test_api_get_billing_accounts(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource)

        # add a value in cache dict to use it in other test cases
        mycache["billing_account_id"] = com_resp.json.get("results")[0].get("billingAccountId")

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    def test_api_get_billing_account_using_id(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNT_BY_ID").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"), billingAccountId=mycache["billing_account_id"]
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    def test_api_get_payment_methods(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("PAYMENT_METHODS").format(
            billingAccountId=mycache["billing_account_id"]
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    def test_api_get_current_costs(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("CURRENT_COSTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"), billingAccountId=mycache["billing_account_id"]
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    def test_api_get_promotions(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"), billingAccountId=mycache["billing_account_id"]
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)
