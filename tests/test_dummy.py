from datetime import datetime

import pytest
from flaky import flaky

# import pytest


# @pytest.mark.test3
# def test_after_cpu_fault_injected_3(get_fault_end_ts):
#     print("Execute test-3")
#     if datetime.now().timestamp() > float(get_fault_end_ts):
#         pytest.skip("*** Skipping test_after_cpu_fault_injected_3 ***")
#     print(get_fault_end_ts)
#     print(datetime.fromtimestamp(float(get_fault_end_ts)))
#     print("in test_after_cpu_fault_injected_3")
#
#
# @pytest.mark.test1
# def test_after_cpu_fault_injected_1(get_fault_end_ts):
#     print("Execute test-1")
#     print(get_fault_end_ts)
#     print(datetime.fromtimestamp(float(get_fault_end_ts)))
#     print("in test_after_cpu_fault_injected_1")


# from tests import conftest


@flaky(max_runs=2, min_passes=1, rerun_filter=None)
@pytest.mark.usefixtures("init_chrome_driver")
class TestDummy:
    def test_example1(self):
        """
        test_example1 description
        Returns:
            None
        """
        print("test_example1 called")
        import time

        # time.sleep(60)

    def test_example2(self):
        """
        test_example2 description
        Returns:
            None
        """
        print("test_example2 called")
        assert 0 == 1

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
