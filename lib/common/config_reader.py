#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" config file parser """

__author__ = "tarun mudgal"

import json
import os


def parse_json(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("json file '%s' does not exist" % file_path)
    with open(file_path) as json_file:
        json_data = json.load(json_file)

    return json_data
