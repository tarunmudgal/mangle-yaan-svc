#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import math

import pytest
import requests

from lib.csp import resources

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_onboarding_service.yaml"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class", LIST_NETWORK_POLICY_FILENAMES, indirect=True,
)
class TestTranslationAPIs(object):
    """
    test cases for language translation APIs when VIP service calls are blocked
    """

    @pytest.mark.dependency()
    def test_api_language_translation_when_VIP_service_calls_are_blocked(
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
        request_body = {"title": "test onboarding", "description": "test onboarding"}

        # verify csp api raises exception for 'too many 504 error responses'
        with pytest.raises(requests.exceptions.RetryError, match=".*too many 504 error responses.*"):
            cclient.make_call("POST", api_resource, json=request_body, retry_count=0)

