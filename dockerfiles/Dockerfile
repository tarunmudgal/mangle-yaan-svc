FROM python:3.6-alpine
MAINTAINER Csp QE Team "csp-pune-qe@vmware.com"

COPY ../lib/common /commons
COPY ../lib/mangle /mangle_lib
COPY ../lib/k8s /k8s_lib
COPY ../config /config
COPY ../tests /tests
COPY ../pytest.ini /
COPY ../requirements.txt /
COPY ../run_tests.sh /

WORKDIR /

RUN pip install -r requirements.txt

ENV project_name csp_resiliency
ENV workload_name cpu_spike
ENV run_id abcd
CMD ["sh", "run_tests.sh"]