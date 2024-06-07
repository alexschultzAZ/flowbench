import yaml
import requests
import argparse
from openfaas_deployment import build_openfaas_stack

class WorkflowProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        self.functions = {}
        self.execution_order = []
        self.workflow_logic_data = {}
        self.workflow_logic = ""
        self.load_template()
        self.build_execution_order()

    def load_template(self):
        with open(self.template_path, 'r') as file:
            template = yaml.safe_load(file)
            self.functions = template['functions']
            self.workflow_logic_data = template['workflow_logic']
            self.workflow_logic = self.workflow_logic_data['name']

    def build_execution_order(self):
        for function_name, details in self.functions.items():
            # print(type(details['order']))
            if 'order' not in details:
                continue
            orderNumber = details['order']
            if len(self.execution_order) < orderNumber:
                self.execution_order.append([details['name']])
            else:
                self.execution_order[orderNumber - 1].append(details['name'])
        print("Execution order data is {}".format(self.execution_order))
    
    def handle_pipeline(self):
        for funcList in self.execution_order:
            if(len(funcList) > 1):
                print("Pipeline workflow cannot have two or more functions at the same level")
                return
            # Call the openfaas function
            # response = requests.get("http://127.0.0.1:8080/function/" + funcList[0])
            print("Called " + funcList[0])
    
    def handle_cron(self):
        for funcList in self.execution_order:
            if(len(funcList) > 1):
                print("Pipeline workflow cannot have two or more functions at the same level")
                return
            # Call the openfaas function
            # response = requests.get("http://127.0.0.1:8080/function/" + funcList[0])
            print("Called " + funcList[0])

    def handle_one_to_many(self):
        # First process the function at level 1
        func = self.execution_order[0][0]

        # response = requests.get("http://127.0.0.1:8080/function/" + func)
        # Dummy invocation
        response = requests.get('https://httpbin.org/status/200')

        if response.status_code == 200:
            print("Request was successful for {} at level 1".format(func))

            # Calling functions at next level only if the first function returns successfully
            print("Now calling the functions at level 2 asynchronously")
            for func in self.execution_order[1]:
                # Call each function ASYNCHRONOUSLY using /async-function
                # response = requests.get("http://127.0.0.1:8080/async-function/" + func)
                print("Called {} asynchronously".format(func))
        else:
            print("Request failed with status code:", response.status_code)
        
        

    def handle_many_to_one(self):
        count  = 0
        for func in self.execution_order[0]:
            # Call each function ASYNCHRONOUSLY using /async-function
            # response = requests.get("http://127.0.0.1:8080/async-function/" + func)
            #use "X-Callback-Url: http://127.0.0.1:5000/async-handler" post request with
            # functions_count and function_name as data

            # Dummy invocation
            response = requests.get('https://httpbin.org/status/200')
            if response.status_code == 200:
                count += 1
                print("Request was successful for {}".format(func))
            else:
                print("Request failed with status code:", response.status_code)
        
        if count == len(self.execution_order[0]):
            # All the functions at level 1 have successfully run
            # therefore calling the many-to-one function at level 2
            func = self.execution_order[1][0]
            # response = requests.get("http://127.0.0.1:8080/function/" + func)
            print("Called the function at level 2 {} successfully".format(func))
            

    def handle_branching(self):
        pass

    def handle_many_to_one_callback():
        pass

    def process_workflow(self):
        match self.workflow_logic:
            case "pipeline":
                print("pipeline")
                self.handle_pipeline()
            case "cron":
                print("cron")
                self.handle_cron()
            case "one_to_many":
                print("one-to-many")
                self.handle_one_to_many()
            case "many_to_one":
                print("many-to-one")
                self.handle_many_to_one()
            case "branching":
                print("branching")
            case _:
                print("error")
    
    def deploy_functions(self):
        # Pass functions dict to the OpenFaaS build/deployment function
        build_openfaas_stack(self.functions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a workflow template file.')

    # Add the argument for the template file
    parser.add_argument('template_file', type=str, help='Path to the workflow template file')

    # Parse the arguments
    args = parser.parse_args()

    # Create the WorkflowProcessor instance with the provided file name
    processor = WorkflowProcessor(args.template_file)
    processor.process_workflow()



#   A , B, C → D Many-to-one

# A → B , C , D One-to-many

# {

# order_1 : [f1, f2, f3],

# order_2 : [f4],

# }

# {

# order_1 : [f1],

# order_2 : [f2, f3, f4],

# }

# Branching

# F1 → if True: F2; else: F3

#  name: branching

# {

# order_1: [f1]

# order_2: [f2, f3]

# }

# if name == branching:

# run order_2 fun based on the results of f1
    