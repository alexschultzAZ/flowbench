export ENDPOINTINPUT=172.17.0.3:9000 \
export PUSHGATEWAY_IP=172.17.0.2:9091 \
export STORAGE_TYPE=obj \
export MN_FS=false \
export ACCELERATION=gpu \
export OUTPUTBUCKET=stage4

docker run -e ENDPOINTINPUT=172.17.0.3:9000 \
-e PUSHGATEWAY_IP=172.17.0.2:9091 \
-e STORAGE_TYPE=obj \
-e MN_FS=false \
-e OUTPUTBUCKET=stage4 \
-e ACCELERATION=gpu \
-p 8080:8080 \
flowbench2024/knative-facerec-final

curl -X POST http://knative-facerec-final.default.10.64.140.43.sslip.io -H "Content-Type: application/json" -d '{"bucketName": "stage3", "fileName": "test_00-stage-2-2024-07-04-20-14-23-859104-va-monolith-77459f7dd5-kspms.jpg"}'

kubectl logs -f $(kubectl get pods --selector=serving.knative.dev/service=knative-facerec-final -o jsonpath='{.items[0].metadata.name}') -c user-container

microk8s enable nvidia \
  --gpu-operator-set validator.driver.env[0].name=DISABLE_DEV_CHAR_SYMLINK_CREATION \
  --gpu-operator-set validator.driver.env[0].value="true"

sudo microk8s disable nvidia 
sudo microk8s helm3 uninstall gpu-operator -n gpu-operator-resources
kubectl delete namespace gpu-operator-resources
rm -rf ~/.cache/helm
sudo microk8s helm3 repo remove nvidia
sudo snap restart microk8s 

kubectl logs nvidia-container-toolkit-daemonset-ljh9f -n gpu-operator-resources -c driver-validation
microk8s enable nvidia --gpu-operator-set validator.driver.env[0].name="DISABLE_DEV_CHAR_SYMLINK_CREATION" --gpu-operator-set validator.driver.env[0].value=true

kubectl get clusterpolicy -n gpu-operator-resources -o yaml
kubectl get clusterpolicy -n gpu-operator-resources -o yaml > policy-new-new.yaml

microk8s helm3 install gpu-operator nvidia/gpu-operator -n gpu-operator-resources --create-namespace \
    --set-string validator.driver.env[0].name=DISABLE_DEV_CHAR_SYMLINK_CREATION \
    --set-string validator.driver.env[0].value=true

    microk8s enable nvidia \
    --gpu-operator-set-as-default-runtime \
    --gpu-operator-set validator.driver.env[0].name=DISABLE_DEV_CHAR_SYMLINK_CREATION \
    --gpu-operator-set validator.driver.env[0].value=true

kubectl describe pod nvidia-operator-validator-rnj7d -n gpu-operator-resources

microk8s enable nvidia \
    --gpu-operator-set-as-default-runtime \
    --gpu-operator-values=policy-new.yaml


Add the following lines to 'gpu-values.yaml'
validator:
  driver:
    env:
      - name: DISABLE_DEV_CHAR_SYMLINK_CREATION
        value: "true"

Run the following command

microk8s enable nvidia --gpu-operator-set-as-default-runtime  --gpu-operator-values=gpu-values.yaml
microk8s enable metallb:10.64.140.43-10.64.140.49