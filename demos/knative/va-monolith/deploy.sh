sudo docker build -t flowbench2024/knative-facextract-new . --push
microk8s kubectl delete -f knative.yml
microk8s kubectl apply -f knative.yml