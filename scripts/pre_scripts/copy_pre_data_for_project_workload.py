#!/usr/bin/env python
import argparse
import os
import sys

import boto3


def check_arg(args=None):
    parser = argparse.ArgumentParser(description="Copy Script")
    parser.add_argument("-p", "--project_name", help="project name", required="True", default="")
    parser.add_argument("-w", "--workload_name", help="workload name", required="True", default="")
    parser.add_argument("-r", "--run_id", help="run_id", required="True", default="")

    results = parser.parse_args(args)
    return (results.project_name, results.workload_name, results.run_id)


class Copy_Inputs_For_Project_Workload(object):
    """
    Copy_Inputs_For_Project_Workload - mainly helps in copying inputs to relevant run_id
    """

    def __init__(self, project_name, workload_name, run_id):
        self.project_name = project_name
        self.workload_name = workload_name
        self.run_id = run_id

    def upload_inputs_to_s3(self):
        """
        This method creates directory on AWS S3
        :param bucket_name: S3 bucket name
        :param directory_name: name of directory to be created on AWS S3
        :return: returns True of directory created successfully
        """
        s3 = boto3.client(
            "s3",
            aws_access_key_id="AKIAUE4JITGQ3LKSAK5E",
            aws_secret_access_key="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",
        )
        print("Uploading results to s3 initiated...")

        bucket_name = "csp-e2e-qe"
        directory_name = (
            "maxim-gun/"
            + self.project_name
            + "/"
            + self.workload_name
            + "/"
            + self.run_id
            + "/inputs"
        )
        s3.put_object(Bucket=bucket_name, Key=(directory_name + "/"))

        input_dir = "inputs/" + self.project_name + "/" + self.workload_name
        print("Local Source:", input_dir)
        print("Dest  S3path:", directory_name)
        try:
            for path, subdirs, files in os.walk(input_dir):
                for file in files:
                    dest_path = path.replace(input_dir, "")
                    s3_file_location = os.path.normpath(
                        directory_name + "/" + dest_path + "/" + file
                    )
                    local_file_location = os.path.join(path, file)
                    print(
                        "Uploading: [",
                        local_file_location,
                        "] to S3 location: [",
                        s3_file_location + "]",
                    )
                    s3.upload_file(local_file_location, bucket_name, s3_file_location)
                    print(" ...Success")
        except Exception as e:
            print(" ... Failed!! Quitting Upload!!")
            print(e)
            raise e


if __name__ == "__main__":
    """
    Usage:
    python copy_pre_data_for_project_workload.py -p project_name -w workload_name -r run_id
    """

    project_name, workload_name, run_id = check_arg(sys.argv[1:])
    Copy_Inputs_For_Project_Workload(project_name, workload_name, run_id).upload_inputs_to_s3()
