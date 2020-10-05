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
COMMERCE["BILLING_ACCOUNTS"] = "/commerce/api/v3/orgs/{orgId}/billing-accounts"
COMMERCE["BILLING_ACCOUNT_BY_ID"] = "/commerce/api/v3/orgs/{orgId}/billing-accounts/{billingAccountId}"
COMMERCE["PAYMENT_METHODS"] = "/commerce/api/v1/orgs/{orgId}/payment-methods"
COMMERCE["CURRENT_COSTS"] = "/commerce/api/v3/orgs/{orgId}/billing-accounts/{billingAccountId}/current-costs"
COMMERCE["PROMOTIONS"] = "/commerce/api/v1/orgs/{orgId}/promotions"

# AM resources
AM = OrderedDict()
AM["AUTHORIZE"] = "/am/api/auth/api-tokens/authorize"
AM["ORGS"] = "/am/api/orgs"
AM["ORG_ROLES"] = "/am/api/orgs/{orgId}/roles"
AM["ORG_CLIENTS"] = "/am/api/orgs/{orgId}/clients"
AM["ORG_USERS"] = "/am/api/orgs/{orgId}/users"
AM["ORG_USERS_V2"] = "/am/api/v2/orgs/{orgId}/users"
AM["ORG_USER_SEARCH"] = "/am/api/orgs/{orgId}/users/search"
AM["ORG_GROUPS"] = "/am/api/orgs/{orgId}/groups"
AM["ORG_DETAIL"] = "/am/api/orgs/{orgId}"
AM["ORG_OAUTH_APPS"] = "/am/api/orgs/{orgId}/oauth-apps"
AM["PRINCIPAL_USER_INFO"] = "/am/api/loggedin/user"
AM["TERMS_OF_SVC_SIGNATURE"] = "/am/api/tos/signatures"
AM["USER_ACCT"] = "/am/api/users/{acct}"
AM["USER_ACCT_V2"] = "/am/api/v2/users/{userId}"
AM["USER_ACCT_SVC_ROLES"] = "/am/api/users/{acct}/orgs/{orgId}/service-roles"
AM["USER_ACCT_SVC_ROLES_V2"] = "/am/api/v2/users/{userId}/orgs/{orgId}/service-roles"
AM["USER_ACCT_ORG_INFO"] = "/am/api/users/{acct}/orgs/{orgId}/info"
AM["USER_ACCT_ORG_INFO_V2"] = "/am/api/v2/users/{userId}/orgs/{orgId}/info"
AM["USER_ACCT_ORG_ROLES"] = "/am/api/users/{acct}/orgs/{orgId}/roles"
AM["USER_ACCT_ORG_ROLES_V2"] = "/am/api/v2/users/{userId}/orgs/{orgId}/roles"
AM["USER_ACCT_ORGS"] = "/am/api/users/{acct}/orgs"
AM["USER_ACCT_ORGS_V2"] = "/am/api/v2/users/{userId}/orgs"
AM["USER_ACCT_ORG_INVITATIONS"] = "/am/api/orgs/invitations/{acct}"

# SLC resources
SLC = OrderedDict()
SLC["SERVICES"] = "/slc/api/v2/orgs/{orgId}/services"
SLC["GET_SVC_DEF"] = "/slc/api/definitions/external/{id}"
SLC["GET_SVC_DEF_ROLES"] = "/slc/api/definitions/external/{id}/service-roles"
SLC["GET_SVC_FAMILIES"] = "/slc/api/family"

# OS resources
OS = OrderedDict()
OS["ONBOARDING_CONTEXTS"] = "/os/api/service-definitions/{serviceDefinitionId}/onboarding-contexts"
OS["ONBOARDING_CONTEXTS_BY_ID"] = "/os/api/service-definitions/{serviceDefinitionId}/onboarding-contexts/{onboardingContextId}"
OS["FAQ_TOPICS"] = "/os/api/service-definitions/{serviceDefinitionId}/faq-topics"
