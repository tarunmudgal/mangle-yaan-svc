#!/usr/bin/env bash
echo $APIKEY
docker login -u mtarun -p $APIKEY vmware-docker-csp-tools.bintray.io

docker build -t vmware-docker-csp-tools.bintray.io/mangle-yaan:latest -f dockerfiles/Dockerfile .
docker push vmware-docker-csp-tools.bintray.io/mangle-yaan:latest