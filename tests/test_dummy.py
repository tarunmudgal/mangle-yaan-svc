import copy
import json
import logging
import random
import time

import pytest



@pytest.mark.parametrize("inject_infra_cpu_fault",[{'cpuload':80,'timeout':30000,'container_name':'csp-data-enrichment','label':'app=csp-data-enrichment'}],indirect=["inject_infra_cpu_fault"])
def test_cluster_status(inject_infra_cpu_fault, request):
    print("Execute test")