#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import os

import pytest
import requests

from lib.csp import resources
from src.testlib.pytest import utils

CURRENT_FILENAME = os.path.basename(__file__)
LIST_DEPENDENT_SERVICES = ["csp-onboarding"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class", LIST_DEPENDENT_SERVICES, indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestCommerceDependencyOnDifferentServices:
    @pytest.mark.dependency()
    def test_api_get_billing_accounts(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = 200

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource)

        # add a value in cache dict to use it in other test cases
        mycache["test_info"][CURRENT_FILENAME] = {}
        mycache["test_info"][CURRENT_FILENAME]["billing_account_id"] = com_resp.json.get("results")[0].get("billingAccountId")

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(
        depends=utils.get_testcase_names(
            "TestCommerceDependencyOnDifferentServices::test_api_get_billing_accounts",
            LIST_DEPENDENT_SERVICES,
        )
    )
    def test_api_get_billing_account_using_id(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNT_BY_ID").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(
        depends=utils.get_testcase_names(
            "TestCommerceDependencyOnDifferentServices::test_api_get_billing_accounts",
            LIST_DEPENDENT_SERVICES,
        )
    )
    def test_api_get_payment_methods(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("ORG_PAYMENT_METHODS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    @pytest.mark.skip(reason="this API is the part of commerce 2.0 and under development")
    @pytest.mark.dependency(
        depends=utils.get_testcase_names(
            "TestCommerceDependencyOnDifferentServices::test_api_get_billing_accounts",
            LIST_DEPENDENT_SERVICES,
        )
    )
    def test_api_get_current_costs(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("CURRENT_COSTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )
        params = {"locale": "en_US"}

        com_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(
        depends=utils.get_testcase_names(
            "TestCommerceDependencyOnDifferentServices::test_api_get_billing_accounts",
            LIST_DEPENDENT_SERVICES,
        )
    )
    def test_api_get_promotions(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code == expected_response
        ), "Commerce service did not return expected response {}".format(expected_response)
