#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" config file parser """

__author__ = "tarun mudgal"

import json
import os


def parse_config(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("config file '%s' does not exist" % file_path)
    with open(file_path) as conf_file:
        conf_data = json.load(conf_file)

    return conf_data
