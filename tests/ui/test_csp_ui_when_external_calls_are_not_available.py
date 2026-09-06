#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import time

import pytest

from src.testlib.selenium.pages.csp.login_page import LoginPage
from src.testlib.selenium.pages.csp.my_account_page import MyAccountPage

USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"

if csp_env == "dev":
    USER = "sscpperfuser1@harakirimail.com"
    PASSWORD = "Test@123"


# def interceptor(request):
#     if request.url == 'https://console-preview.cloud.company.com/csp/gateway/ff-service/api/sdk/public-flags':
#         request.create_response(
#             status_code=503,
#             headers={'Content-Type': 'application/json'},  # Optional headers dictionary
#             body='<html>Hello World!</html>'  # Optional body
#         )


@pytest.mark.usefixtures("init_chrome_driver_with_call_interceptor")
class TestCSPUIWhenExternalCallsBlocked:
    # @pytest.mark.skip(reason="incomplete test case")
    def test_csp_login_logout_when_intercom_call_is_blocked(self, mock_response_interceptor):
        del self.driver.request_interceptor
        del self.driver.requests

        request_url = "https://{host}/csp/gateway/cs/api/loggedin/user/intercom".format(
            host=myconfig.get("csp").get(csp_env).get("host")
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

        ## there was a delay for intercom call to be made on dev and preview env. adding this sleep for dev
        if csp_env == "dev" or csp_env == "preview":
            mylog.info("waiting for 120 seconds before checking requests")
            time.sleep(120)

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

    # @pytest.mark.skip(reason="incomplete test case")
    def test_csp_login_logout_when_feedback_call_is_blocked(self, mock_response_interceptor):
        del self.driver.request_interceptor
        del self.driver.requests

        request_url = "https://feedback.esp-staging.company-aws.com/api/feedback/v1/trigger-events"
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

    # @pytest.mark.skip(reason="incomplete test case")
    def test_csp_login_logout_when_translation_call_is_blocked(self, mock_response_interceptor):
        del self.driver.request_interceptor
        del self.driver.requests

        request_url = "https://{host}/i18n/api/v2/combination/translationsAndPattern".format(
            host=myconfig.get("csp").get(csp_env).get("host")
        )
        request_response = 503
        request_headers = {"Content-Type": "application/json"}
        request_body = "<html>translationsAndPattern call mocked!</html>"
        interceptor_ref = mock_response_interceptor(
            request_url, request_response, request_headers, request_body
        )
        self.driver.request_interceptor = interceptor_ref

        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        my_account_page = MyAccountPage(self.driver, timeout=60)
        my_account_page.goto_my_account_page()
        my_account_page.update_language_preference("Deutsch")
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

        assert is_translation_call_found, "it seems translation call is not found in CSP requests"

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

        del self.driver.request_interceptor
        del self.driver.requests
