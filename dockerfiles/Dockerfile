FROM python:3.6-alpine
MAINTAINER CSP QE Team "csp-pune-qe@vmware.com"

RUN apk add build-base

COPY . /mangle-yaan/

WORKDIR /mangle-yaan

RUN pip install -r /mangle-yaan/dev-requirements.txt

ENV run_id=''
ENV PROJECT_NAME=''
ENV WORKLOAD_NAME=''
ENV TESTSUITE_NAMES=''
ENV PYTEST_ARGS='""'

CMD python /mangle-yaan/test_runner.py \
    --project_name ${PROJECT_NAME} \
    --workload_name ${WORKLOAD_NAME} \
    --testsuite_names ${TESTSUITE_NAMES} \
    --pytest_args ${PYTEST_ARGS}
