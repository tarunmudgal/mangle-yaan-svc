#!/usr/bin/env bash
echo $APIKEY
docker login -u abaheti -p $APIKEY vmware-docker-csp-tools.bintray.io

docker build . -t vmware-docker-csp-tools.bintray.io/csp-resiliency-tests:latest
docker push vmware-docker-csp-tools.bintray.io/csp-resiliency-tests:latest

docker build -f Dockerfile_workload . -t vmware-docker-csp-tools.bintray.io/csp-resiliency-workload-wrapper:latest
docker push vmware-docker-csp-tools.bintray.io/csp-resiliency-workload-wrapper:latest