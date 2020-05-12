FROM python:3.6-alpine
MAINTAINER Csp QE Team "csp-pune-qe@vmware.com"

COPY ./commons /commons
COPY ./mangle_lib /mangle_lib
COPY ./k8s_lib /k8s_lib
COPY ./config /config
COPY ./tests /tests
COPY pytest.ini /
COPY requirements.txt /

WORKDIR /

RUN pip install -r requirements.txt

ENV project_name csp_resiliency
ENV workload_name cpu_spike
ENV run_id abcd

CMD ["pytest", "/tests/test_dummy.py"]