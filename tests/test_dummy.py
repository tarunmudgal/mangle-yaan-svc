from datetime import datetime

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



import pytest

@pytest.mark.usefixtures('create_sut_class')
class TestDummy():
    def test_example1(self):
        print("test_example1 called")

    def test_example2(self):
        print("test_example2 called")
        assert 0 == 1

    def test_example3(self):
        print("test_example3 called")

@pytest.fixture
def create_sut():
    instances = []
    def create_sut(**kwargs):
        s = Sut(**kwargs)
        instances.append(s)
        return s
    yield create_sut
    for s in instances:
        s.cleanup()

@pytest.fixture(scope='class')
def create_sut_class():
    instances = []
    s = Sut(p1='v1')
    instances.append(s)
    print("create_sut_class setup")
    yield
    for s in instances:
        s.cleanup()
    print("create_sut_class teardown")

class Sut:
    """
    Represents system under test

    Provides high-level methods for interaction
    """
    def __init__(self, **kwargs):
        print('DO SETUP')
        self.__dict__.update(kwargs)

    def cleanup(self):
        print('DO CLEANUP')