import pytest
import time
from commons import logger
from mangle_lib.operations.fault_operations import InfraFaultOperations


from mangle_lib.operations.fault_operations import AppFaultOperations

log = logger.setup_logging(__name__)

ROOT_USER = "root"
SCHEDULE_CRON_EXP = None
SCHEDULE_EPOCH_TIME = None
TAGS = {}

@pytest.fixture(scope='function')
def inject_infra_cpu_fault(request):
    # if topology.get_constant('INJECT_FAULT'):
        log.info("Inject CPU Fault via Fixture..")
        # for manager in topology.testbed.vsms:
        ifo = InfraFaultOperations('10.182.50.117','admin@mangle.local','admin','maxim-gun-123','maxim-gun-123','scdc1-staging-trace-it-now')

        schedule_cron_exp = SCHEDULE_CRON_EXP
        if 'schedule_cron_exp' in request.param:
            schedule_cron_exp = request.param['schedule_cron_exp']
        schedule_epoch_time = SCHEDULE_EPOCH_TIME
        if 'schedule_epoch_time' in request.param:
             schedule_epoch_time = request.param['schedule_epoch_time']
        tags = TAGS
        if 'tags' in request.param:
            tags = request.param['tags']

        ifo.inject_fault("CPU", cpuload=request.param['cpuload'],
                             timeout=request.param['timeout'],
                             schedule_cron_exp=schedule_cron_exp,
                             schedule_epoch_time=schedule_epoch_time,
                             tags=tags)

        def tear():
            log.info("Verifying the System status in Teardown")
            time.sleep(request.param['timeout'])
            ifo.verify_nsxt_system()
        request.addfinalizer(tear)