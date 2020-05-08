from commons import logger
from mangle_lib.operations.fault_operations import InfraFaultOperations

log = logger.setup_logging(__name__)

ROOT_USER = "root"
SCHEDULE_CRON_EXP = None
SCHEDULE_EPOCH_TIME = None
TAGS = {}
MANGLE_IP = '10.182.50.117'
MANGLE_USER = 'admin@mangle.local'
MANGLE_PASSWORD = 'admin'


def inject_infra_cpu_fault(request):
    log.info("Inject CPU Fault via Fixture..")
    ifo = InfraFaultOperations(MANGLE_IP, MANGLE_USER, MANGLE_PASSWORD, request['k8s_endpoint'],
                                     request['k8s_credential'], request['k8s_namespace'])

    schedule_cron_exp = SCHEDULE_CRON_EXP
    if 'schedule_cron_exp' in request:
        schedule_cron_exp = request['schedule_cron_exp']
    schedule_epoch_time = SCHEDULE_EPOCH_TIME
    if 'schedule_epoch_time' in request:
        schedule_epoch_time = request['schedule_epoch_time']
    tags = TAGS
    if 'tags' in request:
        tags = request['tags']

    return ifo.inject_fault("CPU", cpuload=request['fault_percentage'],
                     timeout=request['timeout'],
                     container_name=request['container_name'],
                     label=request['container_label'],
                     schedule_cron_exp=schedule_cron_exp,
                     schedule_epoch_time=schedule_epoch_time,
                     tags=tags)

