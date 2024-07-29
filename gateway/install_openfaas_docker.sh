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
set -e

# Function to log in to faas-cli
faas_cli_login() {
  PASSWORD=$1
  echo "Logging in to faas-cli with provided password..."
  echo -n $PASSWORD | faas-cli login --username="admin" --password-stdin || true
}

# Check if the basic-auth secret exists
if kubectl -n openfaas get secret basic-auth; then
  # Secret exists, decode the existing password
  echo "basic-auth secret exists. Decoding the password..."
  PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
  faas_cli_login $PASSWORD
else
  # Secret does not exist, create a new password and secret
  echo "basic-auth secret does not exist. Creating a new one..."
  PASSWORD=$(head -c 12 /dev/urandom | shasum | cut -d' ' -f1)
  kubectl -n openfaas create secret generic basic-auth \
    --from-literal=basic-auth-user=admin \
    --from-literal=basic-auth-password="$PASSWORD"
  faas_cli_login $PASSWORD
fi
tail -f /dev/null
