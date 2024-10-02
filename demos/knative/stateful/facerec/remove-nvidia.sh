sudo microk8s disable nvidia 
sudo microk8s helm3 uninstall gpu-operator -n gpu-operator-resources
sudo microk8s kubectl delete namespace gpu-operator-resources
rm -rf ~/.cache/helm
sudo microk8s helm3 repo remove nvidia
sudo snap restart microk8s 
