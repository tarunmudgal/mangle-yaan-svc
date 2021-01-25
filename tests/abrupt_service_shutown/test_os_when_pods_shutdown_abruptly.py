#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import math
import os

import pytest
import requests

from lib.csp import resources

CURRENT_FILENAME = os.path.basename(__file__)


class TestOnboardingServiceAPIs:
    """

    """

    resource_labels = {"app": "csp-onboarding"}
    random_injection = False
    sleep_interval = 0.5

    def test_api_get_services_for_org(
        self,
    ):  # , inject_k8s_infra_fault_abrupt_pod_shutdown_for_func):
        # expected csp api response (status_code)
        expected_response = [500, 403]

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

        mylog.debug(
            "Onboarding service returned status_code={} that belongs to expected status_code={}".format(
                os_resp.status_code, expected_response
            )
        )

        if os_resp.json is not None:
            # add a value in cache dict to use it in other test cases
            mycache["test_info"][CURRENT_FILENAME] = {}
            mycache["test_info"][CURRENT_FILENAME]["onboarding_context_id"] = os_resp.json.get(
                "onboardingContextId"
            )
