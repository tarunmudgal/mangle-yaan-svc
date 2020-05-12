#!/usr/bin/env python

import os, json, sys, argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from commons.fault_injector import *
import datetime


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Setup Script for a Particular Workload')
    parser.add_argument('-p', '--project_name',
                        help='project name',
                        required='True',
                        default='')
    parser.add_argument('-w', '--workload_name',
                        help='workload name',
                        required='True',
                        default='')
    parser.add_argument('-r', '--run_id',
                        help='run_id',
                        required='True',
                        default='')

    results = parser.parse_args(args)
    return (results.project_name,
            results.workload_name,
            results.run_id)


def write_input_file(project_name, workload_name, env_dict, file_name):
    input_dir = 'inputs/' + project_name + "/" + workload_name

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    with open(input_dir + "/" + file_name, "w") as f:
        f.write(json.dumps(env_dict))


def get_env_var():
    env_dict = dict()

    # Fault params
    env_dict['fault_type'] = os.getenv('fault_type', 'cpuload')
    env_dict['fault_percentage'] = os.getenv('fault_percentage', 30)
    env_dict['timeout'] = os.getenv('timeout', 3000)
    env_dict['container_name'] = os.getenv('container_name', 'csp-customer-support')
    env_dict['container_label'] = os.getenv('container_label', 'app=csp-customer-support')
    env_dict['schedule_cron_exp'] = os.getenv('schedule_cron_exp', None)
    env_dict['schedule_epoch_time'] = os.getenv('schedule_epoch_time', None)
    env_dict['tags'] = os.getenv('tags', None)

    # K8's params
    env_dict['k8s_namespace'] = os.getenv('k8s-namespace', 'csp-app-dev')
    env_dict['k8s_endpoint'] = os.getenv('k8s_endpoint', 'csp-app-dev')
    env_dict['k8s_credential'] = os.getenv('k8s_credential', 'csp-app-dev')

    return env_dict


if __name__ == '__main__':
    '''
    Usage:
    python run.py -p project_name -w workload_name -r run_id
    '''

    project_name, workload_name, run_id = check_arg(sys.argv[1:])

    env_dict = get_env_var()
    log.info("*** Env variable dictionary %s ***", env_dict)

    # Injecting cpu fault
    fault_start_date = datetime.datetime.now()
    print("*******1****")
    print(env_dict)
    if 'cpuload' in env_dict['fault_type']:
        env_dict['fault_id'] = inject_infra_cpu_fault(env_dict)
        log.info("*** env params %s ***", env_dict)
        print(" after generating fault")
        print(env_dict)
    env_dict['fault_start_date'] = str(fault_start_date)
    env_dict['fault_end_timestamp'] = str((fault_start_date + datetime.timedelta(0, int(env_dict['timeout'])/1000)).timestamp())

    log.info("*** Fault %s is injected with Fault Id %s ***", env_dict['fault_type'], env_dict['fault_id'])
    write_input_file(project_name, workload_name, env_dict, 'fault_cpu.csv')