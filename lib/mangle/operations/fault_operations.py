from collections import OrderedDict
import json
import os
import sys

from lib.common import logger

log = logger.setup_logging(__name__)
from lib.mangle import MangleApi
from lib.mangle.operations import EndpointOperations
from lib.mangle.operations.common_operations import CommonOps

lib_path = os.path.abspath(
    os.path.join(__file__, "..", "..", "..", "json_schemas", "remote_machine")
)
sys.path.append(lib_path)
import threading

# constant(s)
VERB_POST = "POST"


class FaultBase(object):
    """
    Fault Operations for API Library
    """

    # Creating separate ordered dict for INFRA fault operations
    infra_faultops_dict = OrderedDict()
    infra_faultops_dict["CPU"] = "generate_cpu_fault"
    infra_faultops_dict["MEMORY"] = "generate_memory_fault"
    infra_faultops_dict["DISKIO"] = "generate_diskio_fault"
    infra_faultops_dict["PROCESSKILL"] = "generate_processkill_fault"
    infra_faultops_dict["FILEHANDLERLEAK"] = "generate_file_handler_leak_fault"
    infra_faultops_dict["KERNELPANIC"] = "generate_kernel_panic_fault"
    infra_faultops_dict["DISKSPACE"] = "generate_diskspace_fault"
    infra_faultops_dict["NETWORK"] = "generate_network_fault"

    # Creating separate ordered dict for APP fault operations
    app_faultops_dict = OrderedDict()
    app_faultops_dict["CPU"] = "generate_cpu_fault"
    app_faultops_dict["MEMORY"] = "generate_memory_fault"
    app_faultops_dict["FILEHANDLERLEAK"] = "generate_file_handler_leak_fault"
    app_faultops_dict["THREADLEAK"] = "generate_thread_leak_fault"

    # Creating a common ordered dict for fault operations which will have both INFRA and APP ordered dicts
    faultops_dict = OrderedDict()
    faultops_dict["INFRA"] = infra_faultops_dict
    faultops_dict["APP"] = app_faultops_dict

    network_fault_map = {
        "DELAY": "NETWORK_DELAY_MILLISECONDS",
        "DUPLICATE": "PACKET_DUPLICATE_PERCENTAGE",
        "CORRUPT": "PACKET_CORRUPT_PERCENTAGE",
        "LOSS": "PACKET_LOSS_PERCENTAGE",
    }

    def __init__(
        self,
        mangle_ip,
        mangle_username,
        mangle_password,
        k8s_endpoint,
        k8s_credential,
        k8s_namespace,
        fault_area,
    ):

        self.mangle_ip = mangle_ip
        self.mangle_username = mangle_username
        self.mangle_password = mangle_password

        # Initialize NSXT Objects
        self.k8s_endpoint = k8s_endpoint
        self.k8s_credential = k8s_credential
        self.k8s_namespace = k8s_namespace

        # Initialize fault area i.e INFRA or APP
        self.fault_area = fault_area

        self.ep_name = "%s" % self.k8s_endpoint
        mylog.debug("%s *** endpoint name is '%s' ***", logger.plugin_name, self.ep_name)
        # set endpoints for fault(s)

        self.cpu_endpoint = "/faults/cpu"
        self.memory_endpoint = "/faults/memory"
        self.kill_process_endpoint = "/faults/kill-process"
        self.diskio_endpoint = "/faults/diskIO"
        self.filehandler_leak_endpoint = "/faults/filehandler-leak"
        self.kernel_panic_endpoint = "/faults/kernel-panic"
        self.diskspace_endpoint = "/faults/disk-space"
        self.network_endpoint = "/faults/network-fault"
        self.thread_leak_endpoint = "/faults/thread-leak"

        # TODO : Endpoint creation to be done after operations is ready
        endpoint_operations = EndpointOperations()
        endpoint_operations.setup_fault_infra(
            self.mangleapi,
            self.k8s_endpoint,
            self.k8s_credential,
            self.k8s_namespace,
            self.ep_name,
        )
        # # get nsxt-object
        # self.nsxt_obj = NSXTVerifiers(self.nsxt_ip, self.nsxt_username,
        #                               self.nsxt_password)

    @property
    def mangleapi(self):
        """
        # TODO:
        """
        return MangleApi(self.mangle_ip, self.mangle_username, self.mangle_password)

    @property
    def nsxtapi(self):
        """
        # TODO:
        """
        return NSXAPI(self.nsxt_ip, self.nsxt_username, self.nsxt_password)

    def inject_fault(self, fault_type, **kwargs):
        """
        # TODO:
        """
        method = self.faultops_dict[self.fault_area][fault_type]
        return getattr(self, method)(**kwargs)

    def inject_daemon_fault(self, fault_type, **kwargs):
        """
        # TODO:
        """
        fault_thread = threading.Thread(target=self.inject_fault, args=fault_type, kwargs=kwargs)
        fault_thread.daemon = True
        fault_thread.start()

    def verify_nsxt_system(self):
        """
        # TODO:
        """

        self.nsxt_obj.verify_services()
        self.nsxt_obj.verify_cores()
        self.nsxt_obj.verify_cluster_status()

    def invoke_mangle_api(self, verb, api_endpoint, payload, fault_area, fault_type):
        """
        # TODO:
        """

        # log the fault injection
        FaultBase._log_fault(fault_area, fault_type, payload)

        ret_val, content = self.mangleapi.make_call(verb, api_endpoint, data=json.dumps(payload))

        print("*****retval and content")
        print(content)

        # wait for fault to get completed
        CommonOps.poll_fault_status(self.mangleapi, content["id"])

        # log the successful completion of fault
        FaultBase._log_fault(fault_area, fault_type, payload, success_msg=1)

        return content["id"]

    @staticmethod
    def _get_json_obj(fname):
        """
        # TODO:
        """
        try:
            with open(fname) as json_file:
                return json.load(json_file)
        except json.decoder.JSONDecodeError as jerr:
            raise Exception("Invalid JSON in body: %s", jerr)

    def get_process_id(self, svc_name):
        """
        # TODO:
        """

        process_identifier = {"corfu": "truststore.password"}

        # build command
        cmd = "ps -ef|awk '$1 == \"%s\"'|grep %s|awk '{print $2}'" % (
            svc_name,
            process_identifier[svc_name],
        )
        mylog.debug(
            "%s *** running command: %s on node %s ***", logger.plugin_name, cmd, self.nsxt_ip
        )
        pid = self.nsxt_obj.get_cli_output(cmd)
        mylog.debug("%s *** pid is %s ***", logger.plugin_name, pid)
        return pid

    @staticmethod
    def set_schedule(schedule_epoch_time, schedule_cron_exp):
        """
        # TODO:
        """
        schedule = {}
        if schedule_cron_exp is not None and schedule_epoch_time is not None:
            raise Exception(
                "%s *** either provide schedule_cron_exp" " or schedule_epoch_time",
                logger.plugin_name,
            )
        elif schedule_cron_exp is None and schedule_epoch_time is None:
            return schedule
        elif schedule_cron_exp is None:
            schedule["timeoutInMilliseconds"] = schedule_epoch_time
        elif schedule_epoch_time is None:
            schedule["cronExpression"] = schedule_cron_exp

        return schedule

    @staticmethod
    def verify_kill_argument(process_name, process_id):
        """
        # TODO:
        """

        if (
            process_name is not None
            and process_id is not None
            and process_name is None
            and process_id is None
        ):
            raise Exception(
                "%s ** either provide process_name or process_id **", logger.plugin_name
            )
        elif process_name is None:
            return process_id
        elif process_id is None:
            return process_name

    @staticmethod
    def _log_fault(fault_area, fault_type, payload, success_msg=0):
        """
        # TODO
        """

        if success_msg:
            mylog.debug(
                "%s *** %s::%s FAULT INJECTED SUCCESSFULLY ***",
                logger.plugin_name,
                fault_area,
                fault_type,
            )
            mylog.banner(
                "%s *** %s::%s FAULT INJECTED SUCCESSFULLY ***",
                logger.plugin_name,
                fault_area,
                fault_type,
            )
        else:
            mylog.banner("%s *** GENERATING %s::%s ***", logger.plugin_name, fault_area, fault_type)
            mylog.debug(
                "%s *** PAYLOAD FOR %s::%s *** \n %s",
                logger.plugin_name,
                fault_area,
                fault_type,
                payload,
            )


class InfraFaultOperations(FaultBase):
    """
    # TODO:
    """

    def __init__(
        self,
        mangle_ip,
        mangle_username,
        mangle_password,
        k8s_endpoint,
        k8s_credential,
        k8s_namespace,
        fault_area="INFRA",
    ):
        super(InfraFaultOperations, self).__init__(
            mangle_ip,
            mangle_username,
            mangle_password,
            k8s_endpoint,
            k8s_credential,
            k8s_namespace,
            fault_area,
        )

    def generate_cpu_fault(
        self,
        cpuload,
        timeout,
        container_name,
        label,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[0]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "cpuLoad": cpuload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.k8s_endpoint,
            "k8sArguments": {
                "containerName": container_name,
                "podLabels": label,
                "enableRandomInjection": True,
            },
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        return self.invoke_mangle_api(
            VERB_POST, self.cpu_endpoint, payload, fault_area, fault_type
        )

    def generate_memory_fault(
        self,
        memoryload,
        timeout,
        container_name,
        label,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[1]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "memoryLoad": memoryload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.k8s_endpoint,
            "k8sArguments": {
                "containerName": container_name,
                "podLabels": label,
                "enableRandomInjection": True,
            },
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(VERB_POST, self.memory_endpoint, payload, fault_area, fault_type)

    def generate_diskio_fault(
        self,
        iosize,
        target_dir,
        timeout,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[2]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "ioSize": iosize,
            "targetDir": target_dir,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(VERB_POST, self.diskio_endpoint, payload, fault_area, fault_type)

    def generate_processkill_fault(
        self,
        process_name=None,
        process_id=None,
        remediation_cmd=None,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """

        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[3]

        # verify kill argument
        kill_arg = FaultBase.verify_kill_argument(process_name, process_id)
        kill_all = None
        if isinstance(kill_arg, str):
            kill_all = True
        if isinstance(kill_arg, int):
            kill_all = False

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "processIdentifier": process_name,
            "processId": process_id,
            "killAll": kill_all,
            "injectionHomeDir": injection_homedir,
            "remediationCommand": remediation_cmd,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(
            VERB_POST, self.kill_process_endpoint, payload, fault_area, fault_type
        )

    def generate_file_handler_leak_fault(
        self,
        timeout,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[4]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(
            VERB_POST, self.filehandler_leak_endpoint, payload, fault_area, fault_type
        )

    def generate_kernel_panic_fault(
        self, injection_homedir="/tmp", schedule_epoch_time=None, schedule_cron_exp=None, tags={}
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[5]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(
            VERB_POST, self.kernel_panic_endpoint, payload, fault_area, fault_type
        )

    def generate_diskspace_fault(
        self,
        diskload,
        target_dir,
        timeout,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[6]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "diskFillSize": diskload,
            "directoryPath": target_dir,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(VERB_POST, self.diskspace_endpoint, payload, fault_area, fault_type)

    def generate_network_fault(
        self,
        nw_fault_type,
        nicname,
        timeout,
        injection_homedir="/tmp",
        latency=None,
        percentage=None,
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict["INFRA"].keys())[7]

        if nw_fault_type == "DELAY" and latency is None:
            raise Exception(
                "%s latency parameter is None for Network delay fault", logger.plugin_name
            )
        elif nw_fault_type != "DELAY" and percentage is None:
            raise Exception(
                "%s percentage parameter is None for Network fault", logger.plugin_name
            )

        payload = {
            "faultOperation": self.network_fault_map[nw_fault_type],
            "nicName": nicname,
            "latency": latency,
            "percentage": percentage,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
        }

        self.invoke_mangle_api(VERB_POST, self.network_endpoint, payload, fault_area, fault_type)


class AppFaultOperations(FaultBase):
    """
    # TODO:
    """

    def __init__(
        self,
        mangle_ip,
        mangle_username,
        mangle_password,
        nsxt_ip,
        nsxt_username,
        nsxt_password,
        fault_area="INFRA",
    ):
        super(AppFaultOperations, self).__init__(
            mangle_ip,
            mangle_username,
            mangle_password,
            nsxt_ip,
            nsxt_username,
            nsxt_password,
            fault_area,
        )

    def generate_cpu_fault(
        self,
        cpuload,
        timeout,
        java_home_path,
        jvm_process,
        user,
        port=9091,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict["APP"].keys())[0]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process)

        payload = {
            "cpuLoad": cpuload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": int(jvm_process),
                "user": user,
                "port": port,
            },
        }

        self.invoke_mangle_api(VERB_POST, self.cpu_endpoint, payload, fault_area, fault_type)

    def generate_memory_fault(
        self,
        memoryload,
        timeout,
        java_home_path,
        jvm_process,
        user,
        port=9091,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict["APP"].keys())[1]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process)

        payload = {
            "memoryLoad": memoryload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": int(jvm_process),
                "user": user,
                "port": port,
            },
        }

        self.invoke_mangle_api(VERB_POST, self.memory_endpoint, payload, fault_area, fault_type)

    def generate_file_handler_leak_fault(
        self,
        timeout,
        java_home_path,
        jvm_process,
        user,
        port=9091,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict["APP"].keys())[2]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process)

        payload = {
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": int(jvm_process),
                "user": user,
                "port": port,
            },
        }

        self.invoke_mangle_api(
            VERB_POST, self.filehandler_leak_endpoint, payload, fault_area, fault_type
        )

    def generate_thread_leak(
        self,
        timeout,
        java_home_path,
        jvm_process,
        user,
        out_of_memory_req=False,
        port=9091,
        injection_homedir="/tmp",
        schedule_epoch_time=None,
        schedule_cron_exp=None,
        tags={},
    ):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict)[1]
        fault_type = list(self.faultops_dict["APP"].keys())[3]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)

        # TODO: this is issue with Mangle itself, can't pass java process name
        # as it unable to handle multiple process with same name
        # will discuss wit Mangle team, and update accordingly
        if isinstance(jvm_process, str):
            mylog.error("%s *** 'jvm_process' pass pid instead of porcess name", logger.plugin_name)
            raise Exception()

        payload = {
            "enableOOM": out_of_memory_req,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.ep_name,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": int(jvm_process),
                "user": user,
                "port": port,
            },
        }

        self.invoke_mangle_api(
            VERB_POST, self.thread_leak_endpoint, payload, fault_area, fault_type
        )
