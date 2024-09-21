sudo docker build -t flowbench2024/knative-facerec-new . --push
microk8s kubectl delete -f service.yml
microk8s kubectl apply -f service.yml