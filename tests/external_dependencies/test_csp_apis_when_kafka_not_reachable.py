#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
import requests

from lib.csp import resources
from src.testlib.csp import utils as csp_utils
from src.testlib.pytest import utils as pytest_utils

LIST_NETWORK_POLICY_FILENAMES = [
    "preview_env_block_egress_from_all_services_to_kafka_message_broker.yaml"
]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class",
    LIST_NETWORK_POLICY_FILENAMES,
    indirect=True,
)
class TestCSPAPIsWhenKafkaServiceNotReachable:
    """
    test cases for CSP APIs when Kafka message broker service calls are blocked
    """

    @pytest.mark.dependency()
    def test_org_user_invitation_api(self, inject_k8s_infra_fault_block_egress_traffic_for_class):
        # expected csp api response (status_code)
        expected_http_code = 200
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_INVITATION").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_org_user_invitation_revoke_api(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 200
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_INVITATION").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {"action": "revoke"}
        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)
