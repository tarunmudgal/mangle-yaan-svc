#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import pytest

from src.testlib.selenium.pages.csp.login_page import LoginPage

USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"
PO_ORG_ID = "1c6f6c98-28bd-47b4-83f6-cad067495fce"
FF_CONFIG_CACHE_UPDATE_INTERVAL = 300


# def interceptor(request):
#     if request.url == 'https://console-preview.cloud.vmware.com/csp/gateway/ff-service/api/sdk/public-flags':
#         request.create_response(
#             status_code=503,
#             headers={'Content-Type': 'application/json'},  # Optional headers dictionary
#             body='<html>Hello World!</html>'  # Optional body
#         )


@pytest.mark.usefixtures("init_chrome_driver_with_call_interceptor")
class TestCSPUIWhenExternalCallsBlocked:
    def test_csp_login_logout_when_intercom_call_is_blocked(self, mock_response_interceptor):
        request_url = (
            "https://console-preview.cloud.vmware.com/csp/gateway/cs/api/loggedin/user/intercom"
        )
        request_response = 503
        request_headers = {"Content-Type": "application/json"}
        request_body = "<html>intercom call mocked!</html>"

        interceptor_ref = mock_response_interceptor(
            request_url, request_response, request_headers, request_body
        )
        self.driver.request_interceptor = interceptor_ref

        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        is_intercom_call_found = False
        for request in self.driver.requests:
            if request.response:
                mylog.debug(
                    "request.url={}, request.response.status_code={}, request.response.headers["
                    "'Content-Type']={}".format(
                        request.url,
                        request.response.status_code,
                        request.response.headers["Content-Type"],
                    )
                )
                if request_url in request.url:
                    assert request.response.status_code == request_response, (
                        "request url {} "
                        "didn't return {} status".format(request_url, request_response)
                    )
                    mylog.debug(
                        "request url {} returned {} status code".format(
                            request_url, request_response
                        )
                    )
                    is_intercom_call_found = True

        assert is_intercom_call_found, "it seems intercom call is not found in CSP requests"

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

        del self.driver.request_interceptor
        del self.driver.requests

    def test_csp_login_logout_when_feedback_call_is_blocked(self, mock_response_interceptor):
        request_url = "https://feedback.esp-staging.vmware-aws.com/api/feedback/v1/trigger-rules"
        request_response = 503
        request_headers = {"Content-Type": "application/json"}
        request_body = "<html>feedback call mocked!</html>"

        interceptor_ref = mock_response_interceptor(
            request_url, request_response, request_headers, request_body
        )
        self.driver.request_interceptor = interceptor_ref

        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        is_feedback_call_found = False
        for request in self.driver.requests:
            if request.response:
                mylog.debug(
                    "request.url={}, request.response.status_code={}, request.response.headers["
                    "'Content-Type']={}".format(
                        request.url,
                        request.response.status_code,
                        request.response.headers["Content-Type"],
                    )
                )
                if request_url in request.url:
                    assert request.response.status_code == request_response, (
                        "request url {} "
                        "didn't return {} status".format(request_url, request_response)
                    )
                    mylog.debug(
                        "request url {} returned {} status code".format(
                            request_url, request_response
                        )
                    )
                    is_feedback_call_found = True

        assert is_feedback_call_found, "it seems feedback call is not found in CSP requests"

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

        del self.driver.request_interceptor
        del self.driver.requests

    @pytest.mark.skip(reason="incomplete test case")
    def test_csp_login_logout_when_translation_call_is_blocked(self, mock_response_interceptor):
        request_url = "https://feedback.esp-staging.vmware-aws.com/api/feedback/v1/trigger-rules"
        request_response = 503
        request_headers = {"Content-Type": "application/json"}
        request_body = "<html>feedback call mocked!</html>"
        interceptor_ref = mock_response_interceptor(
            request_url, request_response, request_headers, request_body
        )
        self.driver.request_interceptor = interceptor_ref

        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        is_translation_call_found = False
        for request in self.driver.requests:
            if request.response:
                mylog.debug(
                    "request.url={}, request.response.status_code={}, request.response.headers["
                    "'Content-Type']={}".format(
                        request.url,
                        request.response.status_code,
                        request.response.headers["Content-Type"],
                    )
                )
                if request_url in request.url:
                    assert (
                        request.response.status_code == request_response
                    ), "request url {} didn't return {} status".format(
                        request_url, request_response
                    )
                    mylog.debug(
                        "request url {} returned {} status code".format(
                            request_url, request_response
                        )
                    )
                    is_translation_call_found = True

        assert is_translation_call_found, "it seems intercom call is not found in CSP requests"

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

        del self.driver.request_interceptor
        del self.driver.requests
