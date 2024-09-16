sudo docker build -t knative-modect:latest .
sudo docker tag knative-modect:latest raghavtiruvallur/knative-modect:latest
sudo docker push raghavtiruvallur/knative-modect:latest
microk8s kubectl delete -f knative.yml
microk8s kubectl apply -f knative.yml