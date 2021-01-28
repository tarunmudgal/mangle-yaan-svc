#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import math
import uuid

import pytest
import requests
from flaky import flaky

from lib.csp import resources

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_onboarding_service.yaml"]


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
class TestCSPAPIsWhenVIPServiceNotReachable:
    """
    test cases for language translation APIs when VIP service calls are blocked
    """

    @pytest.mark.dependency()
    def test_onboarding_contexts_api_when_vip_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 500
        if (
            inject_k8s_infra_fault_block_egress_traffic_for_class
            == "preview_env_egress_onboarding_service.yaml"
        ):
            expected_response = 500

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {
            "seller": "VMWARE",
            "context": {"title": "test context"},
            "description": "patched description",
            "title": "Single Host",
            "globalizationKey": str(uuid.uuid4()),
        }

        # verify csp api raises exception for 'too many 504 error responses'
        with pytest.raises(
            requests.exceptions.RetryError, match=".*too many 504 error responses.*"
        ):
            cclient.make_call("POST", api_resource, json=request_body, retry_count=0)

    @pytest.mark.dependency()
    def test_faq_topics_api_when_vip_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 500
        if (
            inject_k8s_infra_fault_block_egress_traffic_for_class
            == "preview_env_egress_onboarding_service.yaml"
        ):
            expected_response = 500

        # make csp api call
        api_resource = resources.OS.get("FAQ_TOPICS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {
            "linkUrl": "https://jira.eng.vmware.com/",
            "title": "FAQ 13?",
            "linkTitle": "More info",
            "text": "Test description for FAQ 13",
            "onboardingContextIds": ["3c0e2fd2-4dc8-4a01-a356-1ecf2dcd4fbd"],
            "globalizationKey": str(uuid.uuid4()),
        }

        # verify csp api raises exception for 'too many 504 error responses'
        with pytest.raises(
            requests.exceptions.RetryError, match=".*too many 504 error responses.*"
        ):
            cclient.make_call("POST", api_resource, json=request_body, retry_count=0)
