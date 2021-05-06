#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" GameDay Resiliency Service """

__author__ = "tarun mudgal"

import argparse
import builtins
import os.path
import sys
from collections import OrderedDict
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.absolute().as_posix()
builtins.ROOT_DIR = ROOT_DIR
sys.path.append(ROOT_DIR)

from flask import Flask
from flask_restplus import Api, Namespace, Resource, reqparse, inputs

import params
from lib.common import logger
from lib.k8s import k8s_client

# constants initialization


# logger initialization
log = logger.get_logger()
builtins.mylog = log
mylog.info("logger initialized")

# Flask REST service initialization
app = Flask(__name__)
api = Api(
    app,
    version="0.1",
    title="GameDay Resiliency Service",
    description="Resiliency Service that allows Resiliency faults to be injected/remediated into CSP K8S environments",
)

# Authorize namespace
auth_ns = Namespace("gameday/authorize", description="CSP Kubernetes Authorize APIs")
api.add_namespace(auth_ns)

# Internal Service Unavailability namespace
isu_ns = Namespace("gameday/isu", description="Internal Service Unavailability APIs")
api.add_namespace(isu_ns)

# External Service Unavailability namespace
esu_ns = Namespace("gameday/esu", description="External Service Unavailability APIs")
api.add_namespace(esu_ns)


@auth_ns.route("")
class Authorize(Resource):
    def post(self):
        try:
            response = OrderedDict({"message": ""})
            status_code = 200

            req_parser = reqparse.RequestParser()
            req_parser.add_argument(
                "kubeconfig_filepath",
                type=str,
                location="form",
                help="csp namespace kubeconfig file path",
                required=True,
            )
            req_parser.add_argument(
                "namespace", type=str, location="form", help="csp namespace name", required=True,
            )

            args = req_parser.parse_args()
            kubeconfig_filepath = args.get("kubeconfig_filepath")
            namespace = args.get("namespace")

            if not os.path.isfile(kubeconfig_filepath):
                status_code = 404
                response["message"] = "kubeconfig file {} does not exist".format(kubeconfig_filepath)
                return response, status_code

            # config.load_kube_config(config_file=kubeconfig_filepath)
            if params.K8S_CLIENT is None:
                params.K8S_CLIENT = k8s_client.K8SClient(kubeconfig_filepath, namespace)
            params.K8S_NAMESPACE = namespace
            params.K8S_ENV_NAME = namespace.split('-')[2]
            response["message"] = "kubeconfig loaded successfully and K8S client initialized"

        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code


@isu_ns.route("/faults")
class InternalServiceUnavailabilityFaults(Resource):
    # @api.doc(model=run_cmd_model)
    # @api.expect(run_cmd_model)
    @api.doc(
        params={
            "service_name": "service name to be described within a namespace",
            "namespace": "namespace where you want to describe a service",
        }
    )
    def get(self):
        try:
            response = OrderedDict({"message": "", "faulty_services": []})
            status_code = 200

            services_info = params.K8S_CLIENT.list_services()
            for svc_info in services_info.items:
                if svc_info.spec.selector.get("environment", None) == params.FAULTY_SVC_ENV_NAME:
                    params.FAULTY_SVC_NAMES_SET.add(svc_info.metadata.name)

            response.update(
                {
                    "message": "faulty services info fetched successfully",
                    "faulty_services": list(params.FAULTY_SVC_NAMES_SET),
                }
            )
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code

    def post(self):
        try:
            response = OrderedDict({"message": ""})
            status_code = 200

            req_parser = reqparse.RequestParser()
            req_parser.add_argument(
                "service_name",
                type=str,
                location="form",
                help="csp namespace kubeconfig file path",
                required=True,
            )

            args = req_parser.parse_args()
            service_name = args.get("service_name")
            service_info = params.K8S_CLIENT.get_service(service_name)
            if service_info.spec.selector["environment"] != params.FAULTY_SVC_ENV_NAME:
                # mylog.info(
                #     "injecting internal service fault into {} service".format(
                #         service_name
                #     )
                # )
                service_info.spec.selector["environment"] = params.FAULTY_SVC_ENV_NAME
                params.K8S_CLIENT.patch_service(service_name, service_info)
                params.FAULTY_SVC_NAMES_SET.add(service_info.metadata.name)
                # mylog.info(
                #     "internal service fault injected into {} service successfully".format(
                #         service_name
                #     )
                # )
                response["message"] = "internal service fault injected into {} service successfully".format(
                    service_name)
            else:
                status_code = 400
                response["message"] = "internal service fault already exist for {} service".format(
                    service_name)
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code

    def delete(self):
        try:
            response = OrderedDict({"message": "", "remediated_services": []})
            status_code = 200
            remediated_faults = []

            req_parser = reqparse.RequestParser()
            req_parser.add_argument(
                "service_name",
                type=str,
                default=None,
                location="args",
                help="csp namespace kubeconfig file path",
            )
            req_parser.add_argument(
                "remediate_all_faults",
                type=inputs.boolean,
                default=False,
                location="args",
                help="if set, remediates all services ignoring service_name param",
            )

            args = req_parser.parse_args()
            service_name = args.get("service_name")
            remediate_all_faults = args.get("remediate_all_faults")
            if remediate_all_faults:
                services_info = params.K8S_CLIENT.list_services()
                for svc_info in services_info.get('items'):
                    if svc_info.spec.selector["environment"] != params.K8S_ENV_NAME:
                        svc_info.spec.selector["environment"] = params.K8S_ENV_NAME
                        params.K8S_CLIENT.patch_service(service_name, svc_info)
                        remediated_faults.append(svc_info.metadata.name)
                response["message"] = "faulty services are remediated successfully"
            else:
                if service_name is not None:
                    services_info = params.K8S_CLIENT.get_service(service_name)
                    if services_info.spec.selector["environment"] != params.K8S_ENV_NAME:
                        services_info.spec.selector["environment"] = params.K8S_ENV_NAME
                        params.K8S_CLIENT.patch_service(service_name, services_info)
                        remediated_faults.append(services_info.metadata.name)
                        response["message"] = "faulty service {} is remediated successfully".format(services_info.metadata.name)

                    else:
                        status_code = 400
                        response["message"] = "service {} is not faulty".format(service_name)

                else:
                    status_code = 400
                    response[
                        "message"] = "service_name param is required if you want to remediate a specific service else provide remediate_all_faults param with True value"
            response["remediated_services"] = remediated_faults
            params.FAULTY_SVC_NAMES_SET.difference_update(remediated_faults)
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code


def main(port, debug_mode):
    app.run(host="0.0.0.0", port=port, debug=debug_mode)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-p", "--port", default=5000, type=int, help="port number for rest server"
    )
    arg_parser.add_argument(
        "-d",
        "--debug",
        default=False,
        action="store_true",
        help="flag for running gameday resiliency service in debug mode",
    )
    args = arg_parser.parse_args()
    main(args.port, args.debug)
