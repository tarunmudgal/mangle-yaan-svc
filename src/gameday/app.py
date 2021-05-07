#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" GameDay Resiliency Service """

__author__ = "tarun mudgal"

import argparse
import builtins
import json
import os.path
import sys
from collections import OrderedDict
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.absolute().as_posix()
builtins.ROOT_DIR = ROOT_DIR
sys.path.append(ROOT_DIR)

import params
import utils
from flask import Flask
from flask_restplus import Api, Namespace, Resource, inputs, reqparse

from lib.common import logger
from lib.k8s import k8s_client

# constants initialization


# logger initialization
log = logger.get_logger()
builtins.mylog = log
mylog.info("logger initialized")

# Flask REST service app initialization
app = Flask(__name__)
app.config["RESTPLUS_VALIDATE"] = True
app.config.SWAGGER_UI_DOC_EXPANSION = "full"  # allowed values are  ('none', 'list' or 'full')

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
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument(
        "kubeconfig_filepath",
        type=str,
        location="form",
        help="csp namespace kubeconfig file path",
        required=True,
    )
    post_req_parser.add_argument(
        "namespace",
        type=str,
        location="form",
        help="csp namespace name e.g. csp-app-dev",
        required=True,
    )

    @api.expect(post_req_parser)
    def post(self):
        try:
            response = OrderedDict({"message": ""})
            status_code = 200

            args = Authorize.post_req_parser.parse_args()
            kubeconfig_filepath = args.get("kubeconfig_filepath")
            namespace = args.get("namespace")

            if not os.path.isfile(kubeconfig_filepath):
                status_code = 404
                response["message"] = "kubeconfig file {} does not exist".format(
                    kubeconfig_filepath
                )
                return response, status_code

            # config.load_kube_config(config_file=kubeconfig_filepath)
            if params.K8S_CLIENT is None:
                params.K8S_CLIENT = k8s_client.K8SClient(kubeconfig_filepath, namespace)
            params.K8S_NAMESPACE = namespace
            params.K8S_ENV_NAME = namespace.split("-")[2]
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
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument(
        "service_name",
        type=str,
        location="form",
        help="csp namespace kubeconfig file path",
        required=True,
    )

    delete_req_parser = reqparse.RequestParser()
    delete_req_parser.add_argument(
        "service_name",
        type=str,
        default=None,
        location="args",
        help="csp namespace kubeconfig file path",
    )
    delete_req_parser.add_argument(
        "remediate_all_faults",
        type=inputs.boolean,
        default=False,
        location="args",
        help="if set, remediates all services ignoring service_name param",
    )

    def get(self):
        utils.verify_k8s_client()
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

    @api.expect(post_req_parser)
    def post(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict({"message": ""})
            status_code = 200

            args = InternalServiceUnavailabilityFaults.post_req_parser.parse_args()
            service_name = args.get("service_name")
            service_info = params.K8S_CLIENT.get_service(service_name)
            if (
                service_info.spec.selector.get("environment")
                and service_info.spec.selector.get("environment") != params.FAULTY_SVC_ENV_NAME
            ):
                service_info.spec.selector["environment"] = params.FAULTY_SVC_ENV_NAME
                params.K8S_CLIENT.patch_service(service_name, service_info)
                params.FAULTY_SVC_NAMES_SET.add(service_info.metadata.name)
                response[
                    "message"
                ] = "internal service fault injected into {} service successfully".format(
                    service_name
                )
            else:
                status_code = 400
                response["message"] = "internal service fault already exist for {} service".format(
                    service_name
                )
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code

    @api.expect(delete_req_parser)
    def delete(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict({"message": "", "remediated_services": []})
            status_code = 200
            remediated_faults = []

            args = InternalServiceUnavailabilityFaults.delete_req_parser.parse_args()
            service_name = args.get("service_name")
            remediate_all_faults = args.get("remediate_all_faults")
            if remediate_all_faults:
                services_info = params.K8S_CLIENT.list_services()
                for svc_info in services_info.items:
                    if (
                        svc_info.spec.selector.get("environment")
                        and svc_info.spec.selector.get("environment") != params.K8S_ENV_NAME
                    ):
                        svc_info.spec.selector["environment"] = params.K8S_ENV_NAME
                        params.K8S_CLIENT.patch_service(svc_info.metadata.name, svc_info)
                        remediated_faults.append(svc_info.metadata.name)
                response["message"] = "faulty services are remediated successfully"
            else:
                if service_name is not None:
                    services_info = params.K8S_CLIENT.get_service(service_name)
                    if (
                        services_info.spec.selector.get("environment")
                        and services_info.spec.selector.get("environment") != params.K8S_ENV_NAME
                    ):
                        services_info.spec.selector["environment"] = params.K8S_ENV_NAME
                        params.K8S_CLIENT.patch_service(service_name, services_info)
                        remediated_faults.append(services_info.metadata.name)
                        response[
                            "message"
                        ] = "faulty service {} is remediated successfully".format(
                            services_info.metadata.name
                        )

                    else:
                        status_code = 400
                        response["message"] = "service {} is not faulty".format(service_name)

                else:
                    status_code = 400
                    response[
                        "message"
                    ] = "service_name param is required if you want to remediate a specific service else provide remediate_all_faults param with True value"
            response["remediated_services"] = remediated_faults
            params.FAULTY_SVC_NAMES_SET.difference_update(remediated_faults)
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code


@esu_ns.route("/faults")
class ExternalServiceUnavailabilityFaults(Resource):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument(
        "network_policy_name",
        type=str,
        location="form",
        help="network policy filename that needs to be applied",
        required=True,
    )

    delete_req_parser = reqparse.RequestParser()
    delete_req_parser.add_argument(
        "network_policy_name",
        type=str,
        default=None,
        location="args",
        help="network policy name that needs to be deleted",
    )
    delete_req_parser.add_argument(
        "delete_all_nw_policies",
        type=inputs.boolean,
        default=False,
        location="args",
        help="if set, deletes all network policies ignoring network_policy_name param",
    )

    def get(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict({"message": "", "network_policies_found": []})
            status_code = 200
            nw_policies_found = []
            network_policies = params.K8S_CLIENT.list_network_policies()
            for network_policy in network_policies.items:
                nw_policies_found.append(network_policy.metadata.name)

            if nw_policies_found:
                response["message"] = "network policies exist in {} namespace currently".format(
                    params.K8S_NAMESPACE
                )
            else:
                response["message"] = "no network policy exists in {} namespace currently".format(
                    params.K8S_NAMESPACE
                )
            response["network_policies_found"] = nw_policies_found
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code

    @api.expect(post_req_parser)
    def post(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict({"message": ""})
            status_code = 200

            args = ExternalServiceUnavailabilityFaults.post_req_parser.parse_args()
            network_policy_name = args.get("network_policy_name")
            network_policy_filename = (
                params.NETWORK_POLICY_MAP.get(params.K8S_ENV_NAME)
                .get(network_policy_name)
                .get("filename")
            )
            nw_policy_resp, error = params.K8S_CLIENT.create_network_policy(
                network_policy_filename
            )
            if error:
                error_body = json.loads(error.body)
                status_code = error.status
                response["message"] = error_body.get("message")
            else:
                response["message"] = "external service fault {} injected successfully".format(
                    nw_policy_resp.metadata.name
                )
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code

    @api.expect(delete_req_parser)
    def delete(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict(
                {
                    "message": "",
                    "deleted_network_policies": [],
                    "failed_to_delete_network_policies": [],
                }
            )
            status_code = 200
            deleted_nw_policies = []
            failed_to_delete_nw_policies = []

            args = ExternalServiceUnavailabilityFaults.delete_req_parser.parse_args()
            network_policy_name = args.get("network_policy_name")
            delete_all_nw_policies = args.get("delete_all_nw_policies")
            if delete_all_nw_policies:
                network_policies = params.K8S_CLIENT.list_network_policies()
                for nw_policy in network_policies.items:
                    nw_policy_resp, error = params.K8S_CLIENT.delete_network_policy(
                        nw_policy.metadata.name
                    )
                    if error:
                        status_code = error.status
                        failed_to_delete_nw_policies.append(nw_policy.metadata.name)
                    deleted_nw_policies.append(nw_policy.metadata.name)
                if not failed_to_delete_nw_policies:
                    response["message"] = "all network policies deleted successfully"
                else:
                    response[
                        "message"
                    ] = "following network policies could not be deleted: {}".format(
                        failed_to_delete_nw_policies
                    )
            else:
                if network_policy_name is not None:
                    nw_policy_resp, error = params.K8S_CLIENT.delete_network_policy(
                        network_policy_name
                    )
                    if error:
                        error_body = json.loads(error.body)
                        failed_to_delete_nw_policies.append(network_policy_name)
                        status_code = error.status
                        response["message"] = error_body.get("message")
                    else:
                        deleted_nw_policies.append(network_policy_name)
                        response["message"] = "network policy {} is deleted successfully".format(
                            network_policy_name
                        )
                else:
                    status_code = 400
                    response["message"] = (
                        "network_policy_name param is required if you want to delete a specific network "
                        "policy else provide delete_all_nw_policies param with True value"
                    )
            response["deleted_network_policies"] = deleted_nw_policies
            response["failed_to_delete_network_policies"] = failed_to_delete_nw_policies
        except Exception as fault:
            try:
                status_code = fault.code
            except Exception:
                status_code = 500

            response["message"] = "error occurred. Error={}".format(fault)

        return response, status_code


@esu_ns.route("/networkpolicies")
class ExternalServiceUnavailabilityNetworkPolicies(Resource):
    def get(self):
        utils.verify_k8s_client()
        try:
            response = OrderedDict({"message": "", "network_policies": []})
            status_code = 200
            response["message"] = (
                "available networkpolicies are fetched successfully. Please use keys as the network policy name "
                "while creating a network policy using POST /esu/faults call e.g. commerce-deny-external-egress-on-dev"
            )
            response["network_policies"] = params.NETWORK_POLICY_MAP.get(params.K8S_ENV_NAME)
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
