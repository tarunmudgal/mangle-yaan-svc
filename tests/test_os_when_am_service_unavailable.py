#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import pytest
import requests
from lib.csp import resources


@pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_am")
class TestOSDependencyOnAM:
    def test_api_create_onboarding_context(self):
        # expected csp api response (status_code)
        expected_response = requests.codes.ok

        # make csp api call
        api_resource = resources.OS.get("ONBOARDING_CONTEXTS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {
            "title": "test onboarding",
            "description": "test onboarding"
        }

        am_resp = cclient.make_call("POST", api_resource, json=request_body)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
                am_resp.status_code == expected_response
        ), "Onboarding service did not return expected response {}".format(expected_response)
