FROM harbor-repo.vmware.com/dockerhub-proxy-cache/library/python:3.8-alpine
MAINTAINER CSP QE Team "csp-pune-qe@vmware.com"

RUN apk add --update --no-cache \
    python3 \
    python3-dev \
    py-pip \
    build-base \
    openjdk11-jre \
    wget \
    unzip \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*

RUN python -m pip install -U pip
RUN wget https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.13.8/allure-commandline-2.13.8.zip
RUN unzip allure-commandline-2.13.8.zip -d /allure
RUN rm allure-commandline-2.13.8.zip
ENV PATH="/allure/allure-2.13.8/bin:${PATH}"

COPY . /mangle-yaan/

WORKDIR /mangle-yaan

RUN pip install -r /mangle-yaan/dev-requirements.txt

ENV PROJECT_NAME=''
ENV WORKLOAD_NAME=''
ENV TESTSUITE_NAMES=''
ENV PYTEST_ARGS='""'
ENV MYCONFIG='""'
ENV run_id='""'

CMD python /mangle-yaan/test_runner.py \
    --project_name ${PROJECT_NAME} \
    --workload_name ${WORKLOAD_NAME} \
    --testsuite_names ${TESTSUITE_NAMES} \
    --pytest_args ${PYTEST_ARGS:-' '} \
    --myconfig ${MYCONFIG:-' '} \
    --run_id ${run_id:-' '}
