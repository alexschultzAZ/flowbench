import yaml

def convert_faas_to_k8s(openfaas_yaml, config):
    with open(openfaas_yaml, 'r') as stream:
        data = yaml.safe_load(stream)

    functions = data['functions']
    k8s_deployments = []

    for func_name, func_details in functions.items():
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': func_name,
                'namespace': 'openfaas-fn'
            },
            'spec': {
                'strategy':{
                    'type': 'Recreate'
                },
                'replicas': 1,
                'selector': {
                    'matchLabels': {
                        'faas_function': func_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'faas_function': func_name
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': func_name,
                            'image': func_details['image'],
                            'env': [{'name': k, 'value': str(v)} for k, v in func_details.get('environment', {}).items()],
                            'ports': [{
                                'containerPort': 8080,
                                'name': 'http',
                                'protocol': 'TCP'
                            }],
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/_/health',
                                    'port': 8080,
                                    'scheme': 'HTTP'
                                },
                                'initialDelaySeconds': 2,
                                'periodSeconds': 2,
                                'timeoutSeconds': 1,
                                'successThreshold': 1,
                                'failureThreshold': 3
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/_/health',
                                    'port': 8080,
                                    'scheme': 'HTTP'
                                },
                                'initialDelaySeconds': 2,
                                'periodSeconds': 2,
                                'timeoutSeconds': 1,
                                'successThreshold': 1,
                                'failureThreshold': 3
                            },
                            'volumeMounts': [{
                                'mountPath': config['mountPath'],
                                'name': 'local-storage'
                            }]
                        }],
                        'volumes': [{
                            'name': 'local-storage',
                            'persistentVolumeClaim': {
                                'claimName': config['pvcName']
                            }
                        }]
                    }
                }
            }
        }

        if 'constraints' in func_details:
            deployment['spec']['template']['spec']['affinity'] = {
                'nodeAffinity': {
                    'requiredDuringSchedulingIgnoredDuringExecution': {
                        'nodeSelectorTerms': [{
                            'matchExpressions': [{
                                'key': 'kubernetes.io/e2e-az-name',
                                'operator': 'In',
                                'values': func_details['constraints']
                            }]
                        }]
                    }
                }
            }

        k8s_deployments.append(deployment)

    # Convert the list of deployments to a multi-document YAML
    print(k8s_deployments)
    k8s_yaml = yaml.safe_dump_all(k8s_deployments, default_flow_style=False)
    return k8s_yaml

# Example usage
openfaas_yaml_file = '/home/raghav/Desktop/flowbench/demos/video-analytics-revised/video-analytics-revised.yml'
pvc_name = 'local-storage-claim'  # Replace with your PVC name
mount_path = '/mnt/local-storage'  # Replace with your desired mount path in the container

# Convert and print the Kubernetes Deployment YAML
config = {"pvcName" : pvc_name,"mountPath" : mount_path}
k8s_yaml_output = convert_faas_to_k8s(openfaas_yaml_file, config)
print(k8s_yaml_output)
with open('/home/raghav/Desktop/flowbench/demos/video-analytics-revised/kubernetes.yaml', 'w') as f:
    f.write(k8s_yaml_output)
    #yaml.safe_dump(k8s_yaml_output, f, default_flow_style=False)
