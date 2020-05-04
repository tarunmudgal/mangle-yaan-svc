import copy
import json
import logging
import random
import time

import pytest



@pytest.mark.parametrize("inject_infra_cpu_fault",[{'cpuload':90,'timeout':300}],indirect=["inject_infra_cpu_fault"])
def test_cluster_status(inject_infra_cpu_fault, request):
    print("Execute test")