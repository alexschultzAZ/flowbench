#!/bin/bash

set -e

apt update

# Install curl
apt-get install -y curl

# install openfaas cli
curl -sSL https://cli.openfaas.com | sh

if [ $? -eq 0 ]; then
    echo "Successfully installed faas-cli"
else
    echo "Failed to install faas-cli"
fi