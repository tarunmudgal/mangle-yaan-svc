#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from lib.csp import resources as csp_resources


def get_org_details(org_id):
    expected_status_code = 200

    api_resource = csp_resources.AM.get("ORG_DETAIL").format(orgId=org_id)

    resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

    # verify csp api returns expected_status_code
    assert (
        resp.status_code == expected_status_code
    ), "AM service did not return expected status_code={}".format(expected_status_code)

    return resp
