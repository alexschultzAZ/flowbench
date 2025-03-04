import os
import subprocess
import yaml
import datetime
import json
import time
import requests
import argparse
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from knative_deployment import build_and_deploy

class WorkflowProcessor:
    def __init__(self, file_path):
        self.template_path = file_path
        self.functions = []
        self.execution_order = {}
        self.workflow_logic_data = {}
        self.workflow_logic = ""
        self.load_template(file_path=file_path)
        self.build_execution_order()
        # InfluxDB configuration
        url = "http://localhost:8086"         # Update if your InfluxDB endpoint is different
        token = "DMlMCbn3k8jGh_YVWR0EA2G-QkIgikM3xjlLR4svb7eNkiSd1NSFlrMxZJh4rA6hHRpYOpckmLS2bTQFZY4bSA=="           # Replace with your InfluxDB API token
        self.org = "testorg"                        # Replace with your organization name
        self.bucket = "testbucket"                  # Replace with the bucket name you want to write data to

        # Create a client instance
        self.client = InfluxDBClient(url=url, token=token, org=self.org)

        # Get the write API
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def load_template(self, file_path):
        # UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Downloads'))
        with open(file_path, 'r') as file:
            template = yaml.safe_load(file)
            # print(template)
            template_funcs = template['functions']
            for func_name, func_details in template_funcs.items():
                self.functions.append(func_details)
            # print(self.functions)
            self.workflow_logic_data = template['workflow_logic']
            self.workflow_logic = self.workflow_logic_data['name']

    def build_execution_order(self):
        if self.workflow_logic != "branching":
            
            for func_details in self.functions:
                if 'order' not in func_details:
                    continue
                order = 'level' + str(func_details['order'])
                if order in self.execution_order:
                    self.execution_order[order].append(func_details)
                else:
                    self.execution_order[order] = [func_details]
        self.execution_order = dict(sorted(self.execution_order.items()))
        print("Execution order data is {}".format(self.execution_order))
    
    def handle_pipeline(self):
        # prevResponse = {"bucketName" : "stage0", "fileName" : "test_00.mp4"}

        start_time = time.time()
        
        for __, func_list in self.execution_order.items():
            func = func_list[0]
            input_data = func['data']
            if(len(func_list) > 1):
                print("Pipeline workflow cannot have two or more functions at the same level")
                return
            
            service_url = get_knative_service_url(func['name']) 
            # Call the knative function/service
            response = requests.post(service_url, json=input_data)
            print("Response =",response.text)
            input_data = response.text
            print("Called " + func['name'])
            break

        pipeline_end_to_end_time = time.time() - start_time
        point = (
            Point("end_to_end_time")               # measurement name
            # .tag("frame", str(frame))          # optional tag
            .tag("invoc", str(0))
            .field("end_to_end_time", pipeline_end_to_end_time)         # field value
            .time(datetime.datetime.utcnow(), WritePrecision.NS)  # current UTC timestamp
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        print(pipeline_end_to_end_time)

    def stress_pipeline(self, invoc_count):
        # prevResponse = {"bucketName" : "stage0", "fileName" : "test_00.mp4"}

        start_time = time.time()
        
        for __, func_list in self.execution_order.items():
            func = func_list[0]
            input_data = func['data']
            if(len(func_list) > 1):
                print("Pipeline workflow cannot have two or more functions at the same level")
                return
            
            service_url = get_knative_service_url(func['name']) 
            # Call the knative function/service
            response = requests.post(service_url, json=input_data)
            print("Response =",response.text)
            input_data = response.text
            print("Called " + func['name'])
            break

        pipeline_end_to_end_time = time.time() - start_time
        point = (
            Point("end_to_end_time")               # measurement name
            # .tag("frame", str(frame))          # optional tag
            .tag("invoc", str(1))
            .field("end_to_end_time", pipeline_end_to_end_time)         # field value
            .time(datetime.datetime.utcnow(), WritePrecision.NS)  # current UTC timestamp
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        print(pipeline_end_to_end_time)
    
    def handle_cron(self):
        for _, func_list in self.execution_order.items():
            
            # Call the openfaas function
            # response = requests.get("http://127.0.0.1:8080/function/" + func_list[0])
            print("Called " + func_list[0])

    def handle_one_to_many(self):
        # First process the function at level 1
        func = self.execution_order['level1'][0]

        # response = requests.get("http://127.0.0.1:8080/function/" + func)
        # Dummy invocation
        response = requests.get('https://httpbin.org/status/200')

        if response.status_code == 200:
            print("Request was successful for {} at level 1".format(func))

            # Calling functions at next level only if the first function returns successfully
            print("Now calling the functions at level 2 asynchronously")
            for func in self.execution_order['level2']:
                # Call each function ASYNCHRONOUSLY using /async-function
                # response = requests.get("http://127.0.0.1:8080/async-function/" + func)
                print("Called {} asynchronously".format(func))
        else:
            print("Request failed with status code:", response.status_code)
        
        

    def handle_many_to_one(self):
        functions_count = len(self.execution_order['level1'])
        next_function = self.execution_order['level2'][0]
        print("Total \'many\' function count = {}, next_function = {}".format(functions_count, next_function))
        for func in self.execution_order['level1']:
            # Call each function ASYNCHRONOUSLY using /async-functionh
            # functions_count and function_name as data
            # print(f"Request was successful for {func}")
            
            callback_url = f"http://192.168.0.183:5000/async-handler?functions_count={functions_count}&next_function={next_function}"
            response = requests.post(
                f'http://127.0.0.1:8080/async-function/{func}', 
                headers={
                    'X-Callback-Url': callback_url,
                }
            )
            if response.status_code == 202:
                print(f"Request was successful for {func}")
            else:
                print(f"Request failed with status code: {response.status_code}")
            
   
    def validate_conditions(self, conditions):
        valid_operators = ["==", "!=", ">", "<", ">=", "<=", "and", "or"]
        if conditions['operator'] not in valid_operators:
            raise ValueError(f"Invalid operator: {conditions['operator']}")

        if conditions['type'] not in ["int_comparison", "string_comparison", "boolean_comparison"]:
            raise ValueError(f"Invalid condition type: {conditions['type']}")

    def handle_branching(self):
        entry_func = self.workflow_logic_data['entry_func']
        conditions = self.workflow_logic_data['conditions']
        self.validate_conditions(conditions)

        response = requests.get(f"http://127.0.0.1:8080/function/{entry_func}")

        if response.status_code == 200:
            result = response.text.strip()  # assuming the function returns a result as string
            # result = 'False' # assuming the function returns a result as string

            operand = conditions['operand']
            operator = conditions['operator']
            true_func = conditions['true_func']
            false_func = conditions['false_func']
            
            # Perform type conversion if necessary
            if conditions['type'] == "int_comparison":
                try:
                    result = int(result)
                    operand = int(operand)
                except ValueError:
                    raise ValueError(f"Invalid integer comparison between {result} and {operand}")

            elif conditions['type'] == "boolean_comparison":
                try:
                    if type(result) == 'string':
                        result = result.lower() == 'true'
                    if type(operand) == 'string':
                        operand = bool(operand)
                except ValueError:
                    raise ValueError(f"Invalid boolean comparison between {result} and {operand}")

            condition_met = False
            expression = f'{operand} {operator} {result}'
            try:
                condition_met = eval(expression)
                print("Condition met is ", condition_met)
            except ValueError:
                raise ValueError(f"Invalid operator: {operator}")

            next_func = true_func if condition_met else false_func
            response = requests.get(f"http://127.0.0.1:8080/function/{next_func}")
            if response.status_code == 200:
                print(f"Request was successful for {next_func}")
            else:
                print(f"Request failed for {next_func} with status code: {response.status_code}")
        else:
            print(f"Request failed for {entry_func} with status code: {response.status_code}")

    def process_workflow(self):
        if self.workflow_logic == "pipeline":
            print("pipeline")
            self.handle_pipeline()
        elif self.workflow_logic == "cron":
            print("cron")
            self.handle_cron()
        elif self.workflow_logic == "one_to_many":
            print("one-to-many")
            self.handle_one_to_many()
        elif self.workflow_logic == "many_to_one":
            print("many-to-one")
            self.handle_many_to_one()
        elif self.workflow_logic == "branching":
            print("branching")
            self.handle_branching()
        else:
            print("error")

    def stress_workflow(self):
        if self.workflow_logic == "pipeline":
            print("pipeline")
            self.stress_pipeline()
        elif self.workflow_logic == "cron":
            print("cron")
            self.handle_cron()
        elif self.workflow_logic == "one_to_many":
            print("one-to-many")
            self.handle_one_to_many()
        elif self.workflow_logic == "many_to_one":
            print("many-to-one")
            self.handle_many_to_one()
        elif self.workflow_logic == "branching":
            print("branching")
            self.handle_branching()
        else:
            print("error")
    
    def build_and_deploy_functions(self):
        # Pass functions dict to the Knative Helper's build/deployment function
        build_and_deploy(self.functions)

def get_knative_service_url(service_name):
        try:
            # Run the kubectl command to get the name and URL of the service
            result = subprocess.run(
                ['microk8s', 'kubectl', 'get', 'ksvc', service_name, '--output=custom-columns=NAME:.metadata.name,URL:.status.url'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Check if there was an error in the subprocess
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return None

            # Process the output, skip the header line, and get the URL
            output = result.stdout.strip().split('\n')
            if len(output) < 2:
                print("No URL found for the service, cannot proceed exiting..!!!")
                os.exit(1)

            # The second line contains the name and URL
            name, url = output[1].split()
            return url
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a workflow template file.')

    # Add the argument for the template file
    parser.add_argument('template_file', type=str, help='Path to the workflow template file')

    # Parse the arguments
    args = parser.parse_args()

    # Create the WorkflowProcessor instance with the provided file name
    processor = WorkflowProcessor(args.template_file)
    processor.build_and_deploy_functions()
    processor.process_workflow()
    self.client.close()