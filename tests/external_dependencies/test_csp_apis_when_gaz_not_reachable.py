#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
import requests

from lib.csp import resources
from src.testlib.csp import utils as csp_utils
from src.testlib.pytest import utils as pytest_utils

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_am_service.yaml"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class",
    LIST_NETWORK_POLICY_FILENAMES,
    indirect=True,
)
class TestCSPAPIsWhenGAZServiceNotReachable:
    """
    test cases for CSP APIs when GAZ service calls are blocked
    """

    @pytest.mark.dependency()
    def test_get_org_roles_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_GET_ROLES_ERROR"),
            (
                "ACCOUNT_MANAGEMENT_IDP_DRIVER",
                "IDP_ORGANIZATION_GET_ALL_GLOBAL_ORGANIZATION_ROLES_ERROR",
            ),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_ROLES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {"expand": True}

        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_clients_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            (
                "ACCOUNT_MANAGEMENT_IDP_DRIVER",
                "IDP_ORGANIZATION_GET_ALL_GLOBAL_ORGANIZATION_ROLES_ERROR",
            ),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_CLIENTS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_users_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_GET_PAGINATED_USERS_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_USERS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_users_v2_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_GET_PAGINATED_USERS_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_USERS_V2").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_groups_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_GET_GROUPS_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_GROUPS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_search_org_users_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_SEARCH_USERS_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_USER_SEARCH").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {
            "orgId": myconfig.get("csp").get("defaultOrg").get("id"),
            "userSearchTerm": "test",
        }

        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_user_account_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_USER_GET_USER_BY_USER_ID_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("USER_ACCT").format(
            acct=myconfig.get("csp").get("defaultUser").get("email")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_details_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_ORGANIZATION_GET_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_DETAIL").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_org_oauth_apps_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_OAUTH_CSP_GET_OAUTH_CLIENTS_ERROR"),
            ("ACCOUNT_MANAGEMENT_IDP_DRIVER", "IDP_OAUTH_CSP_GET_OAUTH_CLIENTS_ERROR",),
        ]

        # make csp api call
        api_resource = resources.AM.get("ORG_OAUTH_APPS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )

    @pytest.mark.dependency()
    def test_get_principal_user_info_api_when_gaz_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_service_error_types = [
            ("CSP_COMMON", "SERVICE_ERROR"),
            (
                "ACCOUNT_MANAGEMENT_IDP_DRIVER",
                "IDP_USER_GET_USER_BY_USER_ID_ERROR",
                # "IDP_USER_GET_USER_BY_USER_ID_ERROR",
            ),
        ]

        # make csp api call
        api_resource = resources.AM.get("PRINCIPAL_USER_INFO")

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        if resp.json.get("cspErrorCode", None):
            mylog.debug("resp.json={}".format(resp.json))
        module_service_error_types = csp_utils.get_module_service_error_types(
            resp.json.get("cspErrorCode")
        )

        mylog.debug("cspErrorCode={} found in response".format(resp.json.get("cspErrorCode")))
        mylog.debug(
            "module to service error types mapping found as {}".format(module_service_error_types)
        )

        assert (
            resp.status_code == expected_http_code
        ), "AM service did not return expected http status_code={}".format(expected_http_code)

        assert set(module_service_error_types) == set(expected_module_service_error_types), (
            "AM service did not return expected CSP module & service error types mapping. "
            "Actual module_service_error_types={} wherein expected module_service_error_types={}".format(
                module_service_error_types, expected_module_service_error_types
            )
        )
