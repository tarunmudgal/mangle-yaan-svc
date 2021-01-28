#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import math

import pytest
import requests
from flaky import flaky

from lib.csp import resources


@flaky(
    max_runs=myconfig.get("mangleYaan").get("retryFailedTests").get("maxRuns"),
    min_passes=myconfig.get("mangleYaan").get("retryFailedTests").get("minPasses"),
    rerun_filter=None,
)
class TestPaginatedAPIs:
    """
    test cases for paginated response APIs where fault is injected while pages have been read
    """

    @pytest.mark.dependency()
    def test_api_get_oauth_apps_where_am_fault_is_injected_in_one_svc_instance(
        self, inject_k8s_infra_fault_service_unavailable_for_func
    ):
        # expected csp api response (status_code)
        expected_response = 200

        # make csp api call and read first page when fault is not injected
        api_resource = resources.AM.get("ORG_OAUTH_APPS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {
            "OrgId": myconfig.get("csp").get("defaultOrg").get("id"),
            "pageStart": 0,
            "pageLimit": 10,
        }
        cur_page_no = 1

        mylog.info("reading page_no={}".format(cur_page_no))
        am_resp = cclient.make_call("GET", api_resource, params=params)

        # verify csp api actual status_code with expected status code when fault is not injected
        assert (
            am_resp.status_code == expected_response
        ), "AM service did not return expected response {} while reading first page".format(
            expected_response
        )

        # inject service unavailable fault in one am instance after reading first page
        inject_k8s_infra_fault_service_unavailable_for_func("csp-account-management-mvc", True)

        # now, read remaining pages
        total_oauth_apps = am_resp.json.get("totalResults")
        total_pages = math.ceil(total_oauth_apps / params.get("pageLimit"))
        cur_page_no += 1
        while cur_page_no <= total_pages:
            params["pageStart"] += params["pageLimit"]
            mylog.info("reading page_no={}, pageStart={}".format(cur_page_no, params["pageStart"]))
            am_resp = cclient.make_call("GET", api_resource, params=params)

            # verify csp api actual status_code with expected status code when fault is present
            assert (
                am_resp.status_code == expected_response
            ), "AM service did not return expected response {} while reading first page".format(
                expected_response
            )

            cur_page_no += 1

        mylog.info(
            "all pages for oauth-apps have been read successfully even when one of the am service instance was down"
        )
