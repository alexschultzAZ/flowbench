import subprocess
import yaml
import os

combined_yaml_file = 'va-knative-service.yml'

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
    # combined_yaml_file = 'va-knative-service.yml'
    with open(combined_yaml_file, 'w') as file:
        yaml.dump_all(knative_services, file)
    
    return combined_yaml_file

def apply_knative_yaml(yaml_file):
    """Apply the Knative YAML using kubectl."""
    delete_service_command = f"microk8s kubectl delete -f {yaml_file}"
    apply_command = f"microk8s kubectl apply -f {yaml_file}"
    print(f"Deleting Service from {yaml_file}...")
    subprocess.run(delete_service_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Applying {yaml_file}...")
    subprocess.run(apply_command, shell=True, check=True)

def process_functions(input_yaml):
    """Process the functions from the input YAML and handle the Knative deployment."""
    functions = parse_yaml(input_yaml)
    knative_yaml_file = create_knative_services_yaml(functions)

    # Apply the Knative service YAML
    apply_knative_yaml(knative_yaml_file)

       

# Specify the input YAML file (the one you provided)
# input_yaml = 'flowbench_cncf_latest.yml'
input_yaml = 'workflow.yml'
process_functions(input_yaml)
