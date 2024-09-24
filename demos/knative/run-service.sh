#! /bin/bash
microk8s kubectl delete -f $1
microk8s kubectl apply -f $1
