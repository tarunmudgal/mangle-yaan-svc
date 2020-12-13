#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This class covers Onboarding service API test cases where some other service is not available e.g. what does
OS API returns when AM service is not available.

We observed that OS APIs don't have direct dependency on AM service but they do have direct dependency on SLC service
"""

__author__ = "tarun mudgal"

import os

import pytest
import requests

from lib.csp import resources
from src.testlib.pytest import utils

CURRENT_FILENAME = os.path.basename(__file__)
LIST_DEPENDENT_SERVICES = ["csp-account-management-mvc", "csp-service-lifecycle", "csp-commerce"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class", LIST_DEPENDENT_SERVICES, indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestOSDependencyOnDifferentServices:
    @pytest.mark.dependency(name="test_api_create_onboarding_context")
    def test_api_create_onboarding_context(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [201]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [201]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-service-lifecycle":
            expected_response = [500, 502]

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {"title": "test onboarding", "description": "test onboarding"}

        os_resp = cclient.make_call(
            "POST", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.status_code in expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )
        if os_resp.json is not None:
            # add a value in cache dict to use it in other test cases
            mycache["test_info"][CURRENT_FILENAME] = {}
            mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"] = os_resp.json.get(
                "onboardingContextId"
            )

    @pytest.mark.dependency(depends=["test_api_create_onboarding_context"])
    def test_api_get_onboarding_context_using_id(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS_BY_ID").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            onboardingContextId=mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"],
        )

        os_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    def test_api_get_onboarding_contexts(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )

        os_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_create_onboarding_context"])
    def test_api_patch_onboarding_context_using_id(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS_BY_ID").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            onboardingContextId=mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"],
        )

        request_body = {"title": "new test onboarding", "description": "new test onboarding"}

        os_resp = cclient.make_call(
            "PATCH", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    @pytest.mark.dependency(
        name="test_api_create_faq_topics", depends=["test_api_create_onboarding_context"]
    )
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
                "{}".format(mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"])
            ],
            "text": "dummy faq topic",
        }

        os_resp = cclient.make_call(
            "POST", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

        if os_resp.json is not None:
            # add a value in cache dict to use it in other test cases
            mycache["test_info"][CURRENT_FILENAME]["faq_topic_id"] = os_resp.json.get("id")

    def test_api_get_faq_topics(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPICS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )

        os_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_create_faq_topics"])
    def test_api_get_faq_topic(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPIC").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            topicId=mycache["test_info"][CURRENT_FILENAME]["faq_topic_id"],
        )

        os_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_create_faq_topics"])
    def test_api_patch_faq_topic(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPIC").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            topicId=mycache["test_info"][CURRENT_FILENAME]["faq_topic_id"],
        )
        request_body = {
            "title": "new dummy faq topic",
            "onboardingContextIds": [
                "{}".format(mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"])
            ],
            "text": "new dummy faq topic",
        }

        os_resp = cclient.make_call(
            "PATCH", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            os_resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_create_faq_topics"])
    def test_api_delete_faq_topic(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPIC").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id"),
            topicId=mycache["test_info"][CURRENT_FILENAME]["faq_topic_id"],
        )

        os_resp = cclient.make_call("DELETE", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        # assert (
        #         os_resp.json is not None
        # ), "response could not be converted to json. resp.text={}".format(os_resp.text)
        assert (
            os_resp.status_code == expected_response
        ), "Onboarding service returned status_code={} whereas expected status_code={}".format(
            os_resp.status_code, expected_response
        )
