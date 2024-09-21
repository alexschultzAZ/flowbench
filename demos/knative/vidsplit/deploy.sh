sudo docker build -t flowbench2024/knative-vidsplit:latest . --push
microk8s kubectl delete -f knative.yml
microk8s kubectl apply -f knative.yml