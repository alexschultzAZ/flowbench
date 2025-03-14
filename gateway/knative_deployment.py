import subprocess
import yaml
import logging

logging.basicConfig(level=logging.INFO)

def parse_yaml(input_yaml):
    """Parse the input YAML file and extract function details."""
    with open(input_yaml, 'r') as file:
        data = yaml.safe_load(file)
    
    functions = []
    for func in data['do']:
        for func_name, func_details in func.items():
            functions.append({
                'name': func_name,
                'entry': func_details['do'][0]['handle']['entry'],
                'image': func_details['image'],
                'environment': func_details['environment']
            })
    return functions


def create_knative_services_yaml(functions):
    """Create a combined Knative service YAML for all functions."""
    knative_services = []
    logging.debug("Creating Knative Services started")
    for func in functions:
        func_name = func['name']
        image_name = func['image']
        environment = func['environment']
        
        knative_service = {
            'apiVersion': 'serving.knative.dev/v1',
            'kind': 'Service',
            'metadata': {
                'name': func_name,
                'namespace': 'default'
            },
            'spec': {
                'template': {
                    'metadata':{
                        'annotations':{
                            'autoscaling.knative.dev/min-scale': "1",
                            'autoscaling.knative.dev/metric': "concurrency",
                            'autoscaling.knative.dev/target': "20"
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'image': image_name,
                                'env': [{'name': k, 'value': str(v)} for k, v in environment.items()]
                            }
                        ]
                    }
                }
            }
        }
        knative_services.append(knative_service)

    # Write all Knative services to a single YAML file
    result_file = "knative-config.yaml"
    with open(result_file, 'w') as file:
        yaml.dump_all(knative_services, file)
    logging.debug("Creating Knative Services ended")
    
    return result_file

def apply_knative_yaml(yaml_file):
    print("Started Deploying functions onto knative")

    """Apply the Knative YAML using kubectl."""
    delete_service_command = f"microk8s kubectl delete -f {yaml_file}"
    apply_command = f"microk8s kubectl apply -f {yaml_file}"
    print(f"Deleting Service from {yaml_file}...")
    subprocess.run(delete_service_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Applying {yaml_file}...")
    subprocess.run(apply_command, shell=True, check=True)
    logging.info("Applying done!")

def build_and_deploy(functions):
    print("inside build and deploy")
    knative_yaml_file = create_knative_services_yaml(functions)

    # Apply the Knative service YAML
    apply_knative_yaml(knative_yaml_file)

       

