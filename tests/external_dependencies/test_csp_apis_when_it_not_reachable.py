#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest
import requests

from lib.csp import resources
from src.testlib.csp import utils as csp_utils
from src.testlib.pytest import utils as pytest_utils

LIST_NETWORK_POLICY_FILENAMES = ["preview_env_egress_commerce_service.yaml"]


@pytest.mark.parametrize(
    "inject_k8s_infra_fault_block_egress_traffic_for_class",
    LIST_NETWORK_POLICY_FILENAMES,
    indirect=True,
)
class TestCSPAPIsWhenITServiceNotReachable:
    """
    test cases for CSP APIs when IT service calls are blocked
    """

    @pytest.mark.dependency()
    def test_estimated_charges_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"
        if (
            inject_k8s_infra_fault_block_egress_traffic_for_class
            == "preview_env_egress_commerce_service.yaml"
        ):
            expected_http_code = 500
            expected_module_error_type = "CSP_COMMON"
            expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("ESTIMATED_CHARGES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        # verify csp api raises exception for 'too many 500 error responses'
        # with pytest.raises(requests.exceptions.RetryError, match=".*too many 500 error responses.*"):
        #     cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)

        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_offers_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 504

        # make csp api call
        api_resource = resources.COMMERCE.get("OFFERS").format(
            serviceDefinitionId=myconfig.get("csp").get("defaultService").get("id")
        )
        request_body = {"billingEngine": "SAP"}

        resp = cclient.make_call(
            "POST", api_resource, json=request_body, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected_http_code
        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_org_payment_methods_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("ORG_PAYMENT_METHODS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_user_payment_methods_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("USER_PAYMENT_METHODS").format(
            userEmail=myconfig.get("csp").get("defaultUser").get("email")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_promotions_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_list_subscriptions_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 504

        # make csp api call
        api_resource = resources.COMMERCE.get("LIST_SUBSCRIPTIONS")
        params = {"orgId": myconfig.get("csp").get("defaultOrg").get("id")}

        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected_status_code
        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency(
        # depends=pytest_utils.get_testcase_names(
        #     "TestCSPAPIsWhenITServiceNotReachable::test_list_subscriptions_api_when_it_service_calls_are_blocked",
        #     LIST_NETWORK_POLICY_FILENAMES,
        # )
    )
    # @pytest.mark.skipif(mycache["test_csp_apis_when_it_not_reachable_subscriptionId"].get("totalResults") <= 0,
    #                     reason="seems there are no subscriptionIds found")
    def test_get_subscription_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 504

        # make csp api call
        api_resource = resources.COMMERCE.get("GET_SUBSCRIPTION").format(
            subscriptionId="107b5ede-470c-4fd7-9546-de57966aca84"
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected_status_code
        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected status_code={}".format(expected_http_code)

    @pytest.mark.dependency()
    def test_inovice_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("INOVICES").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )

        resp = cclient.make_call("GET", api_resource, retry_count=0, disable_implicit_retry=True)

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_statement_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("SATATEMENT").format(
            orgId=myconfig.get("csp").get("defaultOrg").get("id")
        )
        params = {"count": "15"}

        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )

    @pytest.mark.dependency()
    def test_promotion_type_api_when_it_service_calls_are_blocked(
        self, inject_k8s_infra_fault_block_egress_traffic_for_class
    ):
        # expected csp api response (status_code)
        expected_http_code = 500
        expected_module_error_type = "CSP_COMMON"
        expected_svc_error_type = "SERVICE_ERROR"

        # make csp api call
        api_resource = resources.COMMERCE.get("PROMOTIONS_TYPE")
        params = {"orgId": myconfig.get("csp").get("defaultOrg").get("id"), "promotionType": "ORG"}

        resp = cclient.make_call(
            "GET", api_resource, params=params, retry_count=0, disable_implicit_retry=True
        )

        # verify csp api returns expected error codes
        assert (
            resp.json is not None
        ), "response could not be converted to json. resp.text={}".format(resp.text)
        module_error_code, svc_error_code = resp.json.get("cspErrorCode").split(".")
        module_error_type = csp_utils.get_csp_module_error_code_info(module_error_code).get("type")
        svc_error_type = csp_utils.get_csp_service_error_code_info(
            module_error_code, svc_error_code
        )

        mylog.debug(
            "module_error_type={} found for module_error_code={}".format(
                module_error_type, module_error_code
            )
        )
        mylog.debug(
            "svc_error_type={} found for svc_error_code={}".format(svc_error_type, svc_error_code)
        )

        assert (
            resp.status_code == expected_http_code
        ), "Commerce service did not return expected http status_code={}".format(
            expected_http_code
        )

        assert (
            module_error_type == expected_module_error_type
        ), "Commerce service did not return expected CSP module_error_type={}".format(
            expected_module_error_type
        )
        assert (
            svc_error_type == expected_svc_error_type
        ), "Commerce service did not return expected CSP svc_error_type={}".format(
            expected_svc_error_type
        )
