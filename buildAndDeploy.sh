docker login -u csp-qe-rw-token -p $TOKEN vmwaresaas.jfrog.io
docker build -t vmwaresaas.jfrog.io/csp/mangle-yaan:latest -f dockerfiles/Dockerfile .
docker push vmwaresaas.jfrog.io/csp/mangle-yaan:latest
