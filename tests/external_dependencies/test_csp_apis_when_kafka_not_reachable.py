#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import os

import pytest
import requests
from flaky import flaky

from lib.csp import resources
from src.testlib.csp import utils as csp_utils
from src.testlib.pytest import utils as pytest_utils

LIST_NETWORK_POLICY_FILENAMES = [
    "preview_env_block_egress_from_all_services_to_kafka_message_broker.yaml"
]

CURRENT_FILENAME = os.path.basename(__file__)
SECOND_SERVICE_ID = "142cd4ab-5727-4e7d-9cc2-a87ff8998635"


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
class TestCSPAPIsWhenKafkaServiceNotReachable:
    """
    test cases for CSP APIs when Kafka message broker service calls are blocked
    """

    @pytest.mark.dependency()
    def test_org_user_invitation_api(self, inject_k8s_infra_fault_block_egress_traffic_for_class):
        # expected csp api response (status_code)
        expected_http_code = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_INVITATION").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")
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

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_INVITATION").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")
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

    @pytest.mark.dependency()
    def test_create_service_family(self, inject_k8s_infra_fault_block_egress_traffic_for_class):
        # expected csp api response (status_code)
        expected_http_code = 200

        # make csp api call
        api_resource = resources.SLC.get("SVC_FAMILIES")
        req_body = {
            "description": "res-service-family1",
            "name": "res-service-family1",
            "parentServiceDefinitionId": myconfig.get("csp").get(csp_env).get("defaultService").get("id"),
            "services": [SECOND_SERVICE_ID],
        }

        resp = cclient.make_call(
            "POST", api_resource, json=req_body, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        assert (
            resp.status_code == expected_http_code
        ), "SLC service returned status_code={} whereas expected http status_code={}.".format(
            resp.status_code, expected_http_code
        )

        assert (
            resp.json.get("subServicesIds")[0].get("status") == "PENDING"
        ), "Sub service id={} status is not in " "PENDING state".format(SECOND_SERVICE_ID)

        mycache["test_info"][CURRENT_FILENAME] = {}
        mycache["test_info"][CURRENT_FILENAME]["service_family_id"] = resp.json.get(
            "serviceFamilyId"
        )

    @pytest.mark.dependency(
        depends=pytest_utils.get_testcase_names(
            "TestCSPAPIsWhenKafkaServiceNotReachable::test_create_service_family",
            LIST_NETWORK_POLICY_FILENAMES,
        )
    )
    def test_register_service_family(self, inject_k8s_infra_fault_block_egress_traffic_for_class):
        # expected csp api response (status_code)
        expected_http_code = 200

        # make csp api call
        api_resource = resources.SLC.get("SVC_FAMILY_REGISTER").format(
            serviceFamilyId=mycache["test_info"][CURRENT_FILENAME]["service_family_id"]
        )
        req_body = {"serviceDefinitionId": SECOND_SERVICE_ID}

        resp = cclient.make_call(
            "POST", api_resource, json=req_body, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        assert (
            resp.status_code == expected_http_code
        ), "SLC service did not return expected http status_code={}".format(expected_http_code)

        assert (
            resp.json.get("subServicesIds")[0].get("status") == "ACTIVE"
        ), "Sub service id={} status is not in " "ACTIVE state".format(SECOND_SERVICE_ID)

    @pytest.mark.dependency(
        depends=pytest_utils.get_testcase_names(
            "TestCSPAPIsWhenKafkaServiceNotReachable::test_create_service_family",
            LIST_NETWORK_POLICY_FILENAMES,
        )
    )
    def test_delete_service_family(self, inject_k8s_infra_fault_block_egress_traffic_for_class):
        # expected csp api response (status_code)
        expected_http_code = 200

        # make csp api call
        api_resource = resources.SLC.get("SVC_FAMILY").format(
            serviceFamilyId=mycache["test_info"][CURRENT_FILENAME]["service_family_id"]
        )

        resp = cclient.make_call(
            "DELETE", api_resource, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.status_code == expected_http_code
        ), "SLC service did not return expected http status_code={}".format(expected_http_code)
