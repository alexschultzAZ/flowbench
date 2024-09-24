export ENDPOINTINPUT=172.17.0.3:9000 \
export PUSHGATEWAY_IP=172.17.0.2:9091 \
export STORAGE_TYPE=obj \
export MN_FS=false \
export ACCELERATION=gpu \
export OUTPUTBUCKET=stage4

docker run -e ENDPOINTINPUT=172.17.0.3:9000 \
-e PUSHGATEWAY_IP=172.17.0.2:9091 \
-e STORAGE_TYPE=local \
-e MN_FS=false \
-e OUTPUTBUCKET=stage4 \
-e ACCELERATION=gpu \
-p 8080:8080 \
flowbench2024/knative-facextract-new-test_00 /mnt/local-storage

docker run -e ENDPOINTINPUT=172.17.0.3:9000 \
-e PUSHGATEWAY_IP=172.17.0.2:9091 \
-e STORAGE_TYPE=local \
-e MN_FS=false \
-e OUTPUTBUCKET=stage3 \
-e ACCELERATION=gpu \
-e MOUNT_PATH="/mnt/local-storage" \
-p 8080:8080 \
-v /home/tarun/local_storage:/mnt/local-storage \
flowbench2024/knative-facextract-new-test

curl -X POST http://knative-vidsplit.default.10.64.140.43.sslip.io -H "Content-Type: application/json" -d '{"bucketName": "stage0", "fileName": "test_00.mp4"}'
curl -X POST http://knative-modect.default.10.64.140.43.sslip.io -H "Content-Type: application/json" -d '{"bucketName": "stage1", "fileName": "test_00-stage-1-2024-09-24-23-22-34-814720.zip"}'
curl -X POST http://knative-facextract.default.10.64.140.43.sslip.io -H "Content-Type: application/json" -d '{"bucketName": "stage2", "fileName": ["test_00-2-1-knative-vidsplit-00001-deployment-d7c776d47-ws4dq-2024-09-24-23-22-34-685095-0002.jpg"]}'
curl -X POST http://knative-facerec-final.default.10.64.140.43.sslip.io -H "Content-Type: application/json" -d '{"bucketName": "stage3", "fileName": ["test_00-stage-2-2024-09-24-22-50-27-254119-knative-facextract-00001-deployment-5b9d89bdf5-hxxdq.jpg"]}'
curl -X POST http://172.17.0.4:8080 -H "Content-Type: application/json" -d '{"bucketName": "stage2", "fileName": ["test_00-2-1-knative-vidsplit-00001-deployment-d7c776d47-ws4dq-2024-09-24-23-22-34-685095-0002.jpg"]}'

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


To enable PVC in Knative

kubectl patch --namespace knative-serving configmap/config-features \
 --type merge \
 --patch '{"data":{"kubernetes.podspec-persistent-volume-claim": "enabled", "kubernetes.podspec-persistent-volume-write": "enabled"}}'

 and use readOnly param in volumeMounts and volums in service.yaml
 volumeMounts:
            - name: my-volume
              mountPath: /mnt/local-storage
              readOnly: false
      volumes:
        - name: my-volume
          persistentVolumeClaim:
            claimName: local-storage-claim
            readOnly: false