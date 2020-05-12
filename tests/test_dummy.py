import pytest
from datetime import datetime

# @pytest.mark.parametrize("inject_infra_cpu_fault",[{'cpuload':80,'timeout':30000,'container_name':'csp-data-enrichment','label':'app=csp-data-enrichment'}],indirect=["inject_infra_cpu_fault"])
# def test_cluster_status(inject_infra_cpu_fault, request):
#     print("Execute test")

@pytest.mark.test3
def test_after_cpu_fault_injected_3(get_fault_end_ts):
    print("Execute test-3")
    if datetime.now().timestamp() > float(get_fault_end_ts):
        pytest.skip("*** Skipping test_after_cpu_fault_injected_3 ***")
    print(get_fault_end_ts)
    print(datetime.fromtimestamp(float(get_fault_end_ts)))
    print("in test_after_cpu_fault_injected_3")

@pytest.mark.test1
def test_after_cpu_fault_injected_1(get_fault_end_ts):
    print("Execute test-1")
    print(get_fault_end_ts)
    print(datetime.fromtimestamp(float(get_fault_end_ts)))
    print("in test_after_cpu_fault_injected_1")
#
# @pytest.mark.test2
# def test_after_cpu_fault_injected_2(get_fault_end_ts):
#     print("Execute test-2")
#     print(get_fault_end_ts)
#     print(datetime.fromtimestamp(float(get_fault_end_ts)))
#     print("in test_after_cpu_fault_injected_2")