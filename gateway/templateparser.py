import os
import yaml
import requests
import argparse
from openfaas_deployment import build_openfaas_stack, deploy

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
            self.workflow_logic_data = template['workflow_logic']
            self.workflow_logic = self.workflow_logic_data['name']

    def build_execution_order(self):
        if self.workflow_logic != "branching":
            
            for _, details in self.functions.items():
                if 'order' not in details:
                    continue
                order = 'level' + str(details['order'])
                if order in self.execution_order:
                    self.execution_order[order].append(details['name'])
                else:
                    self.execution_order[order] = [details['name']]
        self.execution_order = dict(sorted(self.execution_order.items()))
        print("Execution order data is {}".format(self.execution_order))

    def handle_pipeline(self):
        for __, funcList in self.execution_order.items():
            # if(len(funcList) > 1):
            #     print("Pipeline workflow cannot have two or more functions at the same level")
            #     return

            # Call the openfaas function
            response = requests.get("http://127.0.0.1:8080/function/" + funcList[0])
            print("Called " + funcList[0])
    
    def handle_cron(self):
        for _, funcList in self.execution_order.items():
            
            # Call the openfaas function
            # response = requests.get("http://127.0.0.1:8080/function/" + funcList[0])
            print("Called " + funcList[0])

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
            
    """
     http://gateway.openfaas:5000
     http://127.0.0.1:5000/async-handler?functions_count={functions_count}&next_function={next_function}
     curl -X POST http://127.0.0.1:8080/async-function/func2  \
          --data '{"function_count": 3, "next_function": "func4"}'  \
              --header "Content-Type: application/json" \
                    --header "X-Callback-Url: http://192.168.0.183:5000/async-handler?functions_count=3&next_function=func2"
    """
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
                self.handle_branching()
            case _:
                print("error")
    
    def build_and_deploy_functions(self):
        # Pass functions dict to the OpenFaaS build/deployment function
        build_openfaas_stack(self.functions)
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
    processor.process_workflow()

