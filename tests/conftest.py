import pytest
import time
from commons import logger
from mangle_lib.operations.fault_operations import InfraFaultOperations
import boto3, json, os

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
    ifo = InfraFaultOperations('10.182.50.117', 'admin@mangle.local', 'admin', 'csp-app-dev', 'csp-app-dev',
                               'csp-app-dev')

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
                     container_name=request.param['container_name'],
                     label=request.param['label'],
                     schedule_cron_exp=schedule_cron_exp,
                     schedule_epoch_time=schedule_epoch_time,
                     tags=tags)

    # def tear():
    #     log.info("Verifying the System status in Teardown")
    #     time.sleep(request.param['timeout'])
    #     ifo.verify_nsxt_system()
    # request.addfinalizer(tear)


project_name = os.getenv('project_name', 'csp_resiliency')
workload_name = os.getenv('workload_name', 'cpu_spike')
run_id = os.getenv('run_id', '121')
input_dir = "maxim-gun/" + project_name + "/" + workload_name + "/" + run_id + "/inputs"


def download_s3_file():
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    print("downloading file from S3")
    s3 = boto3.client('s3', aws_access_key_id='AKIAUE4JITGQ3LKSAK5E',
                      aws_secret_access_key='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')
    s3.download_file('csp-e2e-qe', input_dir + '/fault_cpu.csv', input_dir + '/fault.csv')


@pytest.fixture(scope='session')
def get_fault_end_ts():
    download_s3_file()
    with open(input_dir + '/fault.csv') as f:
        fault_vals = json.loads(f.read())
        yield fault_vals['fault_end_timestamp']
