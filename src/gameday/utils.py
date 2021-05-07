#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = 'tarun mudgal'

import params
import flask
from flask_restplus import errors

def verify_k8s_client():
    status_code = 200
    response = {"message": ""}
    if params.K8S_CLIENT is None:
        response = flask.Response()
        response.status_code = 401
        response.content_type = "application/json"
        response.data = '{"message": "request is not authenticated. Please call POST gameday/authorize first"}'

        raise errors.HTTPException(description="Authentication error. Please call POST gameday/authorize first",
                                   response=response)

