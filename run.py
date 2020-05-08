#!/usr/bin/env python
import argparse
import subprocess
import sys
import shlex
from os import path


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Pre-Post Script')
    parser.add_argument('-t', '--type',
                        help='type',
                        required='True',
                        default='pre')
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
    return (results.type,
            results.project_name,
            results.workload_name,
            results.run_id)


def run_command(command):
    print("\n-------------\nRunning...." + command)
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc


if __name__ == '__main__':
    '''
    Usage:
    python run.py -t pre -p project_name -w workload_name -r run_id
    '''

    type, project_name, workload_name, run_id = check_arg(sys.argv[1:])

    # create a list of commands
    # each command to subprocess.run must be a list of arguments, e.g.
    # ["python", "echo.py", "hello"]
    cmds = []
    if (path.exists(type + "_scripts/" + project_name + "/" + workload_name + "/" + "run.py")):
        print ("Will be running Workload Specific [" + type + "] Step")
        cmds.append("python " +
                    type + "_scripts/" + project_name + "/" + workload_name + "/" + "run.py" +
                    " -p " + project_name + " -w " + workload_name + " -r " + run_id)

    else:
        print ("Will be running the Default [" + type + "] Step")


    # cmds.append("python " +
    #             type + "_scripts/copy_" + type + "_data_for_project_workload.py" +
    #             " -p " + project_name + " -w " + workload_name + " -r " + run_id)
    rc = 0
    for cmd in cmds:
        rc = rc + run_command(cmd)
    if rc != 0:
        sys.exit(rc)
