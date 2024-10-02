#!/bin/bash


sudo microk8s kubectl delete --filename knative-obj.yml
sudo microk8s kubectl apply --filename knative-obj.yml
