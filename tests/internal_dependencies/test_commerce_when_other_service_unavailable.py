#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import os

import pytest
import requests
from flaky import flaky

from lib.csp import resources
from src.testlib.pytest import utils

CURRENT_FILENAME = os.path.basename(__file__)
LIST_DEPENDENT_SERVICES = ["csp-onboarding", "csp-account-management-mvc"]

# TODO : create confulence page with commerce api's internal api call's workflow if it has
# and there response when they ("csp-onboarding", "csp-account-management-mvc") blocked
@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.usefixtures("update_csp_access_token")
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
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNTS").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

        if com_resp.status_code == 200:
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
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("BILLING_ACCOUNT_BY_ID").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    @pytest.mark.skip(reason="https://vmware.slack.com/archives/C1K5Q80SW/p1665400530463819")
    def test_api_get_payment_methods(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("ORG_PAYMENT_METHODS").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    # @pytest.mark.skip(reason="this API is the part of commerce 2.0 and under development")
    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    @pytest.mark.skip(reason="Open Thread : https://vmware.slack.com/archives/C1K5Q80SW/p1664377422413779")
    def test_api_get_current_costs(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500, 502]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("CURRENT_COSTS").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
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
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
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
    def test_api_get_estimated_charges(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500, 502]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [500, 502]

        # make csp api call
        api_resource = resources.COMMERCE.get("ESTIMATED_CHARGES").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")
        )

        com_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency()
    @pytest.mark.skip(reason="https://vmware.slack.com/archives/C1K5Q80SW/p1665400530463819")
    def test_api_get_offers(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        # TODO : even at normal conditions , offers api returning 500 error , internal server error
        # need to verify once the confirmation from IT
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("OFFERS").format(
            serviceDefinitionId=myconfig.get("csp").get(csp_env).get("defaultService").get("id")
        )
        request_body = {"billingEngine": "SAP"}

        com_resp = cclient.make_call(
            "POST", api_resource, json=request_body, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency()
    @pytest.mark.skip(reason="https://vmware.slack.com/archives/C1K5Q80SW/p1665400530463819")
    def test_api_list_subscriptions(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        # TODO : even at normal conditions ,subscription api returning 500 error , internal server error
        # need to verify once the confirmation from IT
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [200]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("LIST_SUBSCRIPTIONS")
        params = {"orgId": myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")}

        com_resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    @pytest.mark.skip(reason="Open Thread : https://vmware.slack.com/archives/C1K5Q80SW/p1664377422413779")
    def test_api_get_invoice(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500, 502, 504]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("INVOICES").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )
        params = {"count": "15"}

        com_resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_get_billing_accounts"])
    @pytest.mark.skip(reason="Open Thread : https://vmware.slack.com/archives/C1K5Q80SW/p1664377422413779")
    def test_api_get_statement(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500, 502, 504]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.COMMERCE.get("STATEMENT").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id"),
            billingAccountId=mycache["test_info"][CURRENT_FILENAME]["billing_account_id"],
        )
        params = {"count": "15"}

        com_resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            com_resp.status_code in expected_response
        ), "Commerce service returned status_code={} whereas expected status_code should be from {}".format(
            com_resp.status_code, expected_response
        )
