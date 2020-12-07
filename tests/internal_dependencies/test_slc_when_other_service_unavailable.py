#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import pytest

from lib.csp import resources

LIST_DEPENDENT_SERVICES = ["csp-onboarding"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class",
    LIST_DEPENDENT_SERVICES,
    indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestSLCDependencyOnDifferentServices:
    def test_api_get_services_for_org(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = 200
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = 200

        # make csp api call
        api_resource = resources.SLC.get("SERVICES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "SLC service did not return expected response {}".format(expected_response)

    def test_api_get_service_definition(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.SLC.get("GET_SVC_DEF").format(
            id=myconfig.get("csp").get("defaultService").get("id")
        )
        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "SLC service did not return expected response {}".format(expected_response)

    def test_api_get_service_definition_roles(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.SLC.get("GET_SVC_DEF_ROLES").format(
            id=myconfig.get("csp").get("defaultService").get("id")
        )
        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "SLC service did not return expected response {}".format(expected_response)

    def test_api_get_service_families(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.SLC.get("SVC_FAMILIES")
        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "SLC service did not return expected response {}".format(expected_response)
