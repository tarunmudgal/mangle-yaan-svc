docker login -u $APIUSER -p $APIKEY companysaas.jfrog.io
docker build -t companysaas.jfrog.io/csp/mangle-yaan:latest -f dockerfiles/Dockerfile .
docker push companysaas.jfrog.io/csp/mangle-yaan:latest
