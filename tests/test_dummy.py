import copy
import json
import logging
import random
import time

import pytest


@pytest.mark.p0
@pytest.mark.parametrize("inject_infra_cpu_fault",[{'cpuload':90,'timeout':300}],indirect=["inject_infra_cpu_fault"])
def test_cluster_status():
    print("Execute test")