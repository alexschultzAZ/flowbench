#!/bin/bash

sudo snap install microk8s --classic

sudo microk8s enable dns
sudo microk8s enable istio
sudo microk8s enable helm

microk8s kubectl apply --filename https://github.com/knative/serving/releases/download/knative-v1.12.1/serving-crds.yaml
microk8s kubectl apply --filename https://github.com/knative/serving/releases/download/knative-v1.12.1/serving-core.yaml

microk8s kubectl apply --filename https://github.com/knative/net-istio/releases/download/knative-v1.12.1/istio.yaml
microk8s kubectl apply --filename https://github.com/knative/net-istio/releases/download/knative-v1.12.1/net-istio.yaml

microk8s kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.15.2/serving-default-domain.yaml

microk8s kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.14.0/eventing-crds.yaml
microk8s kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.14.0/eventing-core.yaml

microk8s kubectl scale deployment istio-ingressgateway --replicas=1 -n istio-system

KUBELET_ARGS_FILE="/var/snap/microk8s/current/args/kubelet"

if ! grep -q "authentication-token-webhook=true" "$KUBELET_ARGS_FILE"; then
    echo "--authentication-token-webhook=true" | sudo tee -a "$KUBELET_ARGS_FILE"
fi

if ! grep -q "authorization-mode=Webhook" "$KUBELET_ARGS_FILE"; then
    echo "--authorization-mode=Webhook" | sudo tee -a "$KUBELET_ARGS_FILE"
fi

if ! grep -q "read-only-port=10255" "$KUBELET_ARGS_FILE"; then
    echo "--read-only-port=10255" | sudo tee -a "$KUBELET_ARGS_FILE"
fi

cd demos/knative
microk8s helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
microk8s helm repo update

RELEASE_NAME="prometheus"
NAMESPACE="default"

if microk8s helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
    echo "Deleting existing Helm release '$RELEASE_NAME' in namespace '$NAMESPACE'..."
    microk8s helm uninstall "$RELEASE_NAME" -n "$NAMESPACE"
else
    echo "No existing release named '$RELEASE_NAME' found in namespace '$NAMESPACE'."
fi
microk8s helm install prometheus prometheus-community/kube-prometheus-stack -n default -f prom-values.yaml

microk8s kubectl apply -f https://raw.githubusercontent.com/knative-extensions/monitoring/main/servicemonitor.yaml

sudo apt install -y tmux

PROMETHEUS_SESSION_NAME="prometheus-port-forward"

if tmux has-session -t $PROMETHEUS_SESSION_NAME 2>/dev/null; then
    echo "The tmux session '$PROMETHEUS_SESSION_NAME' already exists. Deleting it..."
    tmux kill-session -t $PROMETHEUS_SESSION_NAME
fi

tmux new-session -d -s $PROMETHEUS_SESSION_NAME "microk8s kubectl port-forward -n default svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "Started port-forwarding in a new tmux session named '$PROMETHEUS_SESSION_NAME'."
echo "Access the Prometheus dashboard at http://localhost:9090"

echo "To view the port-forwarding session, attach to it by running: tmux attach-session -t $PROMETHEUS_SESSION_NAME"

sudo docker run -d -p 9091:9091 prom/pushgateway

sudo docker run -d -p 9000:9000 -p 9001:9001 --name minio1 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /mnt/data:/data \
  quay.io/minio/minio server /data --console-address ":9001"


KNATIVE_LOCAL_GATEWAY_SESSION="knative-local-gateway"

if tmux has-session -t $KNATIVE_LOCAL_GATEWAY_SESSION 2>/dev/null; then
    echo "The tmux session '$KNATIVE_LOCAL_GATEWAY_SESSION' already exists. Deleting it..."
    tmux kill-session -t $KNATIVE_LOCAL_GATEWAY_SESSION
fi

tmux new-session -d -s $KNATIVE_LOCAL_GATEWAY_SESSION "microk8s kubectl port-forward svc/knative-local-gateway -n istio-system 8080:80"
echo "Started port-forwarding in a new tmux session named '$KNATIVE_LOCAL_GATEWAY_SESSION'."

microk8s enable metallb:10.64.140.43-10.64.140.49

echo "Setup complete!!"
