#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import requests
from lib.csp import resources


class TestCommerceDependencyOverAM:
    def test_api_get_billing_engines(
        self, inject_k8s_infra_fault_service_unavailable
    ):
        expected_response = 200
        task_id = inject_k8s_infra_fault_service_unavailable(
            myconfig.get("k8sCluster").get("endpointName"), "csp-email-management", True
        )

        api_resource = (
            resources.AM.get("ORG_DETAILS") + "/" + myconfig.get("csp").get("defaultOrg").get("id")
        )
        am_resp = cclient.make_call("GET", api_resource)

        try:
            assert (
                am_resp.status_code == expected_response
            ), "commerce service did not return expected response {}".format(expected_response)
        finally:
            # remediate_fault(task_id)
            pass
        mylog.debug("test function done")
