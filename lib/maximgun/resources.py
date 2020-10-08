#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" all api resources (endpoints) hosted by CSP """

__author__ = "tarun mudgal"

from collections import OrderedDict

# MaximGun API prefix
MAXIMGUN_RES_API_PREFIX = "/api"

MAXIMGUN = OrderedDict()
MAXIMGUN["MANGLEYAAN_CONFIG"] = "/res/runtest/mangle-yaan/config"
MAXIMGUN["TASK_STATUS_UPDATE"] = "/history/status"
