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
LIST_DEPENDENT_SERVICES = ["csp-onboarding", "csp-account-management-mvc"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class", LIST_DEPENDENT_SERVICES, indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestCommerceDependencyOnDifferentServices:
    @pytest.mark.dependency(name="test_api_get_billing_accounts")
    def test_api_get_billing_accounts(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

        if com_resp.json is not None:
            # add a value in cache dict to use it in other test cases
            mycache["test_info"][CURRENT_FILENAME] = {}
            mycache["test_info"][CURRENT_FILENAME]["billing_account_id"] = com_resp.json.get(
                "results"
            )[0].get("billingAccountId")

    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    def test_api_get_billing_account_using_id(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNT_BY_ID").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency()
    def test_api_get_payment_methods(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("ORG_PAYMENT_METHODS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.skip(reason="this API is the part of commerce 2.0 and under development")
    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    def test_api_get_current_costs(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("CURRENT_COSTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )
        params = {"locale": "en_US"}

        com_resp = cclient.make_call(
            "GET", api_resource, params=params, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    def test_api_get_promotions(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )
