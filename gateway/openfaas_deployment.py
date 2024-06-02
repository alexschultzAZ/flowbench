import yaml
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
        stack['functions'][function_name] = {}
        stack['functions'][function_name]['lang'] = details["lang"]
        stack['functions'][function_name]['handler'] = details["handler"]
        stack['functions'][function_name]['image'] = details["image"]
        if 'environment' in details:
            print("Environment data found")
            stack['functions'][function_name]['environment'] = details['environment']
            print("Wrote Environment data in YAML")
        if 'annotations' in details:
            print("Annotations data found")
            stack['functions'][function_name]['annotations'] = details['annotations']
            print("Wrote Annotations data in YAML")
    
    # Write the stack to a YAML file
    with open('stack.yml', 'w') as file:
        yaml.safe_dump(stack, file, default_flow_style=False, sort_keys=False)

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout.decode('utf-8'))

def deploy():
    deploy_command = "sudo faas-cli up -f stack.yml --update=true"
    
    print("Deploying functions...")
    run_command(deploy_command)
    
