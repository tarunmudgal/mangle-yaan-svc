#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import math

import pytest
import requests

from lib.csp import resources

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_commerce_service.yaml"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class", LIST_NETWORK_POLICY_FILENAMES, indirect=True,
)
class TestCSPAPIsWhenITServiceNotReachable(object):
    """
    test cases for commerce APIs when IT service calls are blocked
    """

    @pytest.mark.dependency()
    def test_estimated_charges_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_response = 500
        if (
            inject_k8s_infra_fault_block_egress_traffic_for_class
            == "preview_env_egress_commerce_service.yaml"
        ):
            expected_response = 500

        # make csp api call
        api_resource = resources.COMMERCE.get("ESTIMATED_CHARGES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        # verify csp api raises exception for 'too many 500 error responses'
        with pytest.raises(requests.exceptions.RetryError, match=".*too many 500 error responses.*"):
            cclient.make_call("GET", api_resource, retry_count=0)

