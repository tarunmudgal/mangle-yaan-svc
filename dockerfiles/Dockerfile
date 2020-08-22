FROM python:3.6-alpine
MAINTAINER CSP QE Team "csp-pune-qe@vmware.com"

RUN apk add build-base

COPY . /mangle-yaan/

WORKDIR /mangle-yaan

RUN pip install -r /mangle-yaan/dev-requirements.txt

ENV project_name csp_resiliency
ENV workload_name cpu_spike
ENV run_id abcd
ENV TESTRUNNER_PARAMS /mangle-yaan/tests/test_dummy.py

CMD python /mangle-yaan/test_runner.py ${TESTRUNNER_PARAMS}