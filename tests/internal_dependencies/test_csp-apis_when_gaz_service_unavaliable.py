#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytest service unavailability test cases """

import pytest
from flaky import flaky

from lib.csp import resources


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
@pytest.mark.usefixtures("update_csp_access_token")
@pytest.mark.parametrize(
    "inject_k8s_infra_fault_service_unavailable_for_class", ["csp-gaz-core"], indirect=True,
)
class TestCspapiDependencyOnGazServices:
    def test_api_get_org_detail(self, inject_k8s_infra_fault_service_unavailable_for_class):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call
        api_resource = resources.AM.get("ORG_DETAIL").format(
            orgId=myconfig.get("csp").get(csp_env).get("defaultOrg").get("id")
        )

        am_resp = cclient.make_call("GET", api_resource)

        # verify csp api actual status_code with expected status code when fault is present
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {}".format(expected_response)
