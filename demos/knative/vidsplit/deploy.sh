sudo docker build -t knative-vidsplit:latest .
sudo docker tag knative-vidsplit:latest raghavtiruvallur/knative-vidsplit:latest
sudo docker push raghavtiruvallur/knative-vidsplit:latest
microk8s kubectl delete -f knative.yml
microk8s kubectl apply -f knative.yml