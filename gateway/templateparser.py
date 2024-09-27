import os
import yaml
import json
import requests
import argparse
from gateway.knative_deployment import build_knative_yaml, deploy

class WorkflowProcessor:
    def __init__(self, file_path):
        self.template_path = file_path
        self.functions = {}
        self.execution_order = {}
        self.workflow_logic_data = {}
        self.workflow_logic = ""
        self.load_template(file_path=file_path)
        self.build_execution_order()

    def load_template(self, file_path):
        # UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Downloads'))
        with open(file_path, 'r') as file:
            template = yaml.safe_load(file)
            # print(template)
            self.functions = template['functions']
            self.workflow_logic = self.workflow_logic_data['name']
            

    
    def build_and_deploy_functions(self):
        # Pass functions dict to the OpenFaaS build/deployment function
        build_knative_yaml(self.functions)
        deploy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a workflow template file.')

    # Add the argument for the template file
    parser.add_argument('template_file', type=str, help='Path to the workflow template file')

    # Parse the arguments
    args = parser.parse_args()

    # Create the WorkflowProcessor instance with the provided file name
    processor = WorkflowProcessor(args.template_file)
    processor.build_and_deploy_functions()
    # processor.process_workflow() --- GATEWAY NO LONGER HANDLING CONTROL FLOW - USER TRIGGERS FIRST FUNCTION ETC..

