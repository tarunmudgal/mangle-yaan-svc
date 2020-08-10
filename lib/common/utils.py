#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" utility functions """

__author__ = 'tarun mudgal'

import functools


def log_args(func):
    @functools.wraps(func)
    def _log_args(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = ["{}={}".format(k, v) for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        mylog.debug("func {}({}) called".format(func.__name__, signature))
        return func(*args, **kwargs)
    return _log_args

def verify_status(do_log=True, success_status_range=(200,299)):
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
                    mylog.debug("func call {}({}) status: PASS".format(func.__name__, signature))
                status = True
            else:
                if do_log:
                    mylog.error("func call {}({}) status: FAIL".format(func.__name__, signature))
                    mylog.debug("response: {}".format(response))
            return status, response

        return func_wrapper

    return _verify_response