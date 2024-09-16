sudo docker build -t knative-facextract:latest .
sudo docker tag knative-facextract:latest raghavtiruvallur/knative-facextract:latest
sudo docker push raghavtiruvallur/knative-facextract:latest
microk8s kubectl delete -f knative.yml
microk8s kubectl apply -f knative.yml