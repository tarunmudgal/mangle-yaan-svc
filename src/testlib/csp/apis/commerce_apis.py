#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

from lib.csp import resources as csp_resources


def get_payment_methods(org_id):
    api_resource = csp_resources.COMMERCE.get("ORG_PAYMENT_METHODS").format(orgId=org_id)
    resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

    return resp
