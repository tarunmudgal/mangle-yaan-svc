#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" utility functions """

__author__ = "tarun mudgal"

import functools
import sys
import logging


def log_args(func):
    @functools.wraps(func)
    def _log_args(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = ["{}={}".format(k, v) for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        mylog.debug("func {}({}) called".format(func.__name__, signature))
        return func(*args, **kwargs)

    return _log_args


def verify_status(do_log=True, return_status=True, success_status_range=(200, 299)):
    def _verify_response(func):
        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = ["{}={}".format(k, v) for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            response = func(*args, **kwargs)

            status = False
            if success_status_range[0] <= response.status_code <= success_status_range[1]:
                if do_log:
                    mylog.debug("func {}({}) status: PASS".format(func.__name__, signature))
                status = True
            else:
                if do_log:
                    mylog.error("func {}({}) status: FAIL".format(func.__name__, signature))
                    mylog.debug("response: {}".format(response))
            if return_status:
                return status, response
            return response

        return func_wrapper

    return _verify_response
