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

def test_example1(create_sut):
    sut = create_sut(role='some_role')
    assert sut.role == 'some_role'


def test_example2(create_sut):
    sut = create_sut(name='sut1-uat')
    assert sut.name == 'sut1-uat'

def test_example3(create_sut):
    pass

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