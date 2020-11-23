#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"


def get_testcase_names(name, params):
    def vstr(val):
        if isinstance(val, (list, tuple)):
            return "-".join([str(v) for v in val])
        else:
            return str(val)

    return ["%s[%s]" % (name, vstr(v)) for v in params]
