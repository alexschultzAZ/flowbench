#!/bin/bash

set -e

apt update

# Install curl
apt-get install -y curl

# install openfaas cli
curl -sSL https://cli.openfaas.com | sh

# installing 
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
mv ./kubectl /usr/local/bin/kubectl


curl -sSL https://get.arkade.dev | sh

# arkade get faas-cli

arkade install cron-connector

# install docker
curl -fsSL https://get.docker.com | sh

# Log in to Docker
echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin

# generate password for faas-cli
export PASSWORD=$(head -c 12 /dev/urandom | shasum | cut -d' ' -f1)
kubectl -n openfaas create secret generic basic-auth \
  --from-literal=basic-auth-user=admin \
  --from-literal=basic-auth-password="$PASSWORD"

# Log in to faas-cli
echo -n $PASSWORD | faas-cli login --username="admin" --password-stdin