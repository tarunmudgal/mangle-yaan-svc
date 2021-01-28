#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import pytest
import requests
from flaky import flaky

from lib.csp import resources


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class",
    ["csp-commerce", "csp-onboarding"],
    indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")  # we can use fixture this way
# as well (looks beautiful as no need to pass fixture name to each test case) but it wouldn't allow testcase to get
# fixture's return value at run time
class TestAMDependencyOnDifferentServices:
    def test_api_get_org_roles(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-commerce":
            expected_response = 200
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_ROLES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {"expand": True}

        am_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_clients(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_CLIENTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_users(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_USERS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_users_v2(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_USERS_V2").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_groups(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_GROUPS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_search_org_users(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_SEARCH").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        params = {
            "orgId": myconfig.get("csp").get("defaultOrg").get("id"),
            "userSearchTerm": "test",
        }

        am_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_orgs(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORGS")

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_detail(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_DETAIL").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_oauth_apps(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_OAUTH_APPS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_principal_user_info(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("PRINCIPAL_USER_INFO")

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_terms_of_service_signatures(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("TERMS_OF_SVC_SIGNATURE")

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_user_account(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT").format(
            acct=myconfig.get("csp").get("defaultUser").get("email")
        )

        params = {"expandProfile": True}

        am_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_user_account_v2(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_V2").format(
            userId=myconfig.get("csp").get("defaultUser").get("id")
        )

        params = {"expandProfile": True}

        am_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_svc_roles_for_user_account(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_SVC_ROLES").format(
            acct=myconfig.get("csp").get("defaultUser").get("email"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_svc_roles_for_user_account_v2(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_SVC_ROLES_V2").format(
            userId=myconfig.get("csp").get("defaultUser").get("id"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_info_for_user_account(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORG_INFO").format(
            acct=myconfig.get("csp").get("defaultUser").get("email"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_info_for_user_account_v2(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORG_INFO_V2").format(
            userId=myconfig.get("csp").get("defaultUser").get("id"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_roles_for_user_account(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORG_ROLES").format(
            acct=myconfig.get("csp").get("defaultUser").get("email"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_org_roles_for_user_account_v2(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORG_ROLES_V2").format(
            userId=myconfig.get("csp").get("defaultUser").get("id"),
            orgId=myconfig.get("csp").get("defaultOrg").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_orgs_for_user_account(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORGS").format(
            acct=myconfig.get("csp").get("defaultUser").get("email")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_orgs_for_user_account_v2(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORGS_V2").format(
            userId=myconfig.get("csp").get("defaultUser").get("id"),
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)

    def test_api_get_all_invitations_for_user_account(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT_ORG_INVITATIONS").format(
            acct=myconfig.get("csp").get("defaultUser").get("email")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)
