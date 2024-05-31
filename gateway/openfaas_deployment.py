import yaml
import requests
import subprocess


def build_openfaas_stack(functions):
    # Template for the OpenFaaS stack
    stack = {
        'version': '1.0',
        'provider': {
            'name': 'openfaas',
            'gateway': 'http://127.0.0.1:8080'
        },
        'functions': {}
    }
    
    
    for function_name, details in functions.items():
        stack['functions'][function_name] = {
            'lang': details["lang"],
            'handler': f'{details["handler"]}',
            'image': f'{details["image"]}'
        }
    
    # Write the stack to a YAML file
    with open('stack.yml', 'w') as file:
        yaml.dump(stack, file, default_flow_style=False, sort_keys=False)

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout.decode('utf-8'))

def deploy():
    publish_command = "sudo faas-cli publish -f stack.yml"
    deploy_command = "sudo faas-cli deploy -f stack.yml --update=true"
    
    # Run the commands
    print("Publishing functions...")
    run_command(publish_command)
    
    print("Deploying functions...")
    run_command(deploy_command)
    
