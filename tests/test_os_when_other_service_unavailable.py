#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import pytest
import requests
from lib.csp import resources


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class",
    ["csp-account-management-mvc", "csp-onboarding"],
    indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestOSDependencyOnDifferentServices(object):

    @pytest.mark.dependency()
    def test_api_create_onboarding_context(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 201
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = 201
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = 201

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {
            "title": "test onboarding",
            "description": "test onboarding"
        }

        os_resp = cclient.make_call("POST", api_resource, json=request_body)

        # add a value in cache dict to use it in other test cases
        mycache["onboarding_context_id"] = os_resp.json.get("onboardingContextId")

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(depends=["TestOSDependencyOnAM::test_api_create_onboarding_context"])
    def test_api_get_onboarding_context_using_id(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS_BY_ID").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            onboardingContextId=mycache["onboarding_context_id"])

        os_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)

    def test_api_get_onboarding_contexts(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )

        os_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(depends=["TestOSDependencyOnAM::test_api_create_onboarding_context"])
    def test_api_patch_onboarding_context_using_id(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS_BY_ID").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            onboardingContextId=mycache["onboarding_context_id"])

        request_body = {
            "title": "new test onboarding",
            "description": "new test onboarding"
        }

        os_resp = cclient.make_call("PATCH", api_resource, json=request_body)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)

    @pytest.mark.dependency(depends=["TestOSDependencyOnAM::test_api_create_onboarding_context"])
    def test_api_create_faq_topics(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 201

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPICS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )

        request_body = {
            "linkUrl": "https://dummyurl.com",
            "title": "dummy faq topic",

            "linkTitle": "dummy faq topic",
            "onboardingContextIds": [
                "{}".format(mycache["onboarding_context_id"])
            ],
            "text": "dummy faq topic"
        }

        os_resp = cclient.make_call("POST", api_resource, json=request_body)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)

    def test_api_get_faq_topics(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPICS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )

        os_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                os_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)
