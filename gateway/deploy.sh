#!/bin/bash

docker build . -t ribsmocha/gateway
docker push ribsmocha/gateway
microk8s kubectl apply -f flaskapp-deployment.yaml