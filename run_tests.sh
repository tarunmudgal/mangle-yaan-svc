#!/usr/bin/env bash

pytest tests/test_dummy.py --html=report.html

python commons/upload_report.py
