#!/bin/bash


sudo microk8s kubectl delete --filename service.yaml
sudo microk8s kubectl apply --filename service.yaml
