docker login -u $APIUSER -p $APIKEY vmwaresaas.jfrog.io
docker build -t vmwaresaas.jfrog.io/csp/mangle-yaan:latest -f dockerfiles/Dockerfile .
docker push vmwaresaas.jfrog.io/csp/mangle-yaan:latest
