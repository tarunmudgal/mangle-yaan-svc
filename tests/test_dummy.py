from datetime import datetime

import pytest
from flaky import flaky

import pytest

from src.testlib.selenium.pages.csp.login_page import LoginPage

USER = "lhruser3usd@yahoo.com"
PASSWORD = "Test@123"
PO_ORG_ID = "1c6f6c98-28bd-47b4-83f6-cad067495fce"
FF_CONFIG_CACHE_UPDATE_INTERVAL = 300



def interceptor(request):
    if request.url == 'https://console-preview.cloud.vmware.com/csp/gateway/ff-service/api/sdk/public-flags':
        request.create_response(
            status_code=503,
            headers={'Content-Type': 'application/json'},  # Optional headers dictionary
            body='<html>Hello World!</html>'  # Optional body
        )

# @pytest.mark.test1
# def test_after_cpu_fault_injected_1(get_fault_end_ts):
#     print("Execute test-1")
#     print(get_fault_end_ts)
#     print(datetime.fromtimestamp(float(get_fault_end_ts)))
#     print("in test_after_cpu_fault_injected_1")


# from tests import conftest


# @flaky(max_runs=2, min_passes=1, rerun_filter=None)
@pytest.mark.usefixtures("init_chrome_driver")
# @pytest.mark.usefixtures("init_chrome_driver_with_call_interceptor")
class TestDummy:
    @pytest.mark.skip(reason="incomplete test case")
    def test_example1(self):
        """
        test_example1 description
        Returns:
            None
        """
        print("test_example1 called")
        self.driver.request_interceptor = interceptor
        self.driver.get('https://console-preview.cloud.vmware.com')
        for request in self.driver.requests:
            if request.response:
                print(
                    request.url,
                    request.response.status_code,
                    request.response.headers['Content-Type']
                )
                if 'csp/gateway/ff-service/api/sdk/public-flags' in request.url:
                    assert request.response.status_code == 503, "API csp/gateway/ff-service/api/sdk/public-flags " \
                                                                "didn't return 503 status"
                    mylog.debug("API csp/gateway/ff-service/api/sdk/public-flags returned 503 status code")

    @pytest.mark.skip(reason="incomplete test case")
    def test_example2(self):
        """
        test_example2 description
        Returns:
            None
        """
        # print("test_example2 called")
        # assert 0 == 1
        breakpoint()
        loginpage = LoginPage(self.driver, timeout=60)
        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))

        logout_status = loginpage.do_logout()
        assert logout_status, "user {} could not logout from CSP portal".format(USER)
        mylog.debug("user {} logged-out from CSP portal successfully".format(USER))

        login_status = loginpage.do_login(USER, PASSWORD)
        assert login_status, "user {} could not login to CSP portal".format(USER)
        mylog.debug("user {} logged-in to CSP portal successfully".format(USER))




    def test_example3(self):
        """
        test_example3 description
        Returns:
            None
        """
        print("test_example3 called")

    def test_example4(self):
        """
        test_example4 description
        Returns:
            None
        """
        print("test_example4 called")

    def test_example5(self):
        """
        test_example5 description
        Returns:
            None
        """
        print("test_example5 called")

    def test_example6(self):
        """
        test_example6 description
        Returns:
            None
        """
        print("test_example6 called")
        self.driver.get("https://google.com")
        assert False


# @pytest.fixture
# def create_sut():
#     instances = []
#
#     def create_sut(**kwargs):
#         s = Sut(**kwargs)
#         instances.append(s)
#         return s
#
#     yield create_sut
#     for s in instances:
#         s.cleanup()
#
#
# @pytest.fixture(scope="class")
# def create_sut_class():
#     instances = []
#     s = Sut(p1="v1")
#     instances.append(s)
#     print("create_sut_class setup")
#     yield
#     for s in instances:
#         s.cleanup()
#     print("create_sut_class teardown")
#
#
# class Sut:
#     """
#     Represents system under test
#
#     Provides high-level methods for interaction
#     """
#
#     def __init__(self, **kwargs):
#         print("DO SETUP")
#         self.__dict__.update(kwargs)
#
#     def cleanup(self):
#         print("DO CLEANUP")
