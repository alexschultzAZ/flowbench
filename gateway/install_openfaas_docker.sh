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


# curl -sSL https://get.arkade.dev | sh

# arkade get faas-cli

# arkade install cron-connector

# install docker
curl -fsSL https://get.docker.com | sh


