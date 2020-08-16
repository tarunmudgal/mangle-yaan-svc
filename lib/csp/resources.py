#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" all api resources (endpoints) hosted by CSP """

__author__ = "tarun mudgal"

from collections import OrderedDict

# CSP API prefix
API_PREFIX = "/csp/gateway"

# commerce resources
COMMERCE = OrderedDict()
COMMERCE["BILLING_ENGINES"] = "/commerce/api/v1/orgs/billing-engines"


# AM resources
AM = OrderedDict()
AM["AUTHORIZE"] = "/am/api/auth/api-tokens/authorize"
AM["ORG_DETAILS"] = "/am/api/orgs"

# SLC resources
SLC = OrderedDict()
SLC["SERVICES"] = "/slc/api/v2/orgs/{orgId}/services"
SLC["GET_SVC_DEF"] = "/slc/api/definitions/external/{id}"
SLC["GET_SVC_DEF_ROLES"] = "/slc/api/definitions/external/{id}/service-roles"
SLC["GET_SVC_FAMILIES"] = "/slc/api/family"