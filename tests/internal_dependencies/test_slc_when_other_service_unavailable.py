#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

__author__ = "tarun mudgal"

import os

import pytest
from flaky import flaky

from lib.csp import resources

CURRENT_FILENAME = os.path.basename(__file__)
LIST_DEPENDENT_SERVICES = ["csp-account-management-mvc", "csp-onboarding"]


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.usefixtures("update_csp_access_token")
@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class", LIST_DEPENDENT_SERVICES, indirect=True,
)
# @pytest.mark.usefixtures("inject_k8s_infra_fault_service_unavailable_for_class")
class TestSLCDependencyOnDifferentServices:
    def test_api_get_services_for_org(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]
        if inject_k8s_infra_fault_service_unavailable_for_class == "csp-account-management-mvc":
            expected_response = [500]
        elif inject_k8s_infra_fault_service_unavailable_for_class == "csp-onboarding":
            expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("SERVICES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_get_service_definition(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("GET_SVC_DEF").format(
            id=myconfig.get("csp").get("defaultService").get("id")
        )
        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_get_service_definition_roles(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("GET_SVC_DEF_ROLES").format(
            id=myconfig.get("csp").get("defaultService").get("id")
        )
        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_get_service_families(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("SVC_FAMILIES")
        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_create_operational_data(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200, 409]

        # make csp api call
        api_resource = resources.SLC.get("OPERATIONAL_DATA").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id")
        )

        request_body = {
            "serviceEscalationProcedure": "Use Pagerduty and Slack channel #vmc-assist",
            "serviceCostCenter": "US1079608",
            "serviceEngineeringOwnerEmail": "test@vmware.com",
            "pagerDutyEscalationPolicy": "CSP-ENG-PRODUCTION",
            "status": "PRODUCTION_AVAILABLE",
            "serviceAdditionalKeyContactsEmail": "test@vmware.com",
        }

        slc_resp = cclient.make_call(
            "POST", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_patch_operational_data(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("OPERATIONAL_DATA").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id")
        )

        request_body = {
            "serviceEscalationProcedure": "Updated: Use Pagerduty and Slack channel #vmc-assist"
        }

        slc_resp = cclient.make_call(
            "PATCH", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_get_operational_data(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("OPERATIONAL_DATA").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id")
        )

        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    def test_api_get_all_operational_data(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("ALL_OPERATIONAL_DATA")

        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    @pytest.mark.dependency(name="test_api_create_service_instance")
    def test_api_create_service_instance(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [201]

        # make csp api call
        api_resource = resources.SLC.get("SERVICE_INSTANCES").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {"url": "https://dummyurl.com", "displayName": "res test svc instance"}

        slc_resp = cclient.make_call(
            "POST", api_resource, json=request_body, disable_implicit_retry=True
        )

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

        if slc_resp.json is not None:
            # add a value in cache dict to use it in other test cases
            mycache["test_info"][CURRENT_FILENAME] = {}
            mycache["test_info"][CURRENT_FILENAME]["service_instance_id"] = slc_resp.json.get("id")

    def test_api_get_service_instances(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("SERVICE_INSTANCES").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id")
        )

        slc_resp = cclient.make_call("GET", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )

    @pytest.mark.dependency(depends=["test_api_create_service_instance"])
    def test_api_delete_service_instance(
        self, inject_k8s_infra_fault_service_unavailable_for_class
    ):
        # expected csp api response (status_code)
        expected_response = [200]

        # make csp api call
        api_resource = resources.SLC.get("SERVICE_INSTANCE").format(
            serviceId=myconfig.get("csp").get("defaultService").get("id"),
            instanceId=mycache["test_info"][CURRENT_FILENAME]["service_instance_id"],
        )

        slc_resp = cclient.make_call("DELETE", api_resource, disable_implicit_retry=True)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            slc_resp.status_code in expected_response
        ), "SLC service returned status_code={} whereas expected status_code={}".format(
            slc_resp.status_code, expected_response
        )
