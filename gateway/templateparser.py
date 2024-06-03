import yaml
from openfaas_deployment import build_openfaas_stack

class WorkflowProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        self.functions = {}
        self.workflow_logic_data = {}
        self.workflow_logic = ""
        self.load_template()

    def load_template(self):
        with open(self.template_path, 'r') as file:
            template = yaml.safe_load(file)
            self.functions = template['functions']
            self.workflow_logic_data = template['workflow_logic']
            self.workflow_logic = self.workflow_logic_data['name']
    
    def handle_pipeline(self, f):
        # Until there is no next_function (end of the pipeline), process each function in the sequence
        while True:
            print("Processed function - {}".format(f['name']))
            # Process each function (example placeholder)
            # response = requests.get("http://127.0.0.1:8080/function/" + f['name'])
            if 'next_function' not in f or f['next_function'] is None:
                break
            f = self.functions[f['next_function']]
    
    def handle_cron(self, f):
        while True:
            print("Processed function - {}".format(f['name']))
            # Process each function (example placeholder)
            # response = requests.get("http://127.0.0.1:8080/function/" + f['name'])
            if 'next_function' not in f or f['next_function'] is None:
                break
            f = self.functions[f['next_function']]
    def process_workflow(self):
        entry_point = None
        if 'entry_point' in self.workflow_logic_data:
            entry_point = self.workflow_logic_data["entry_point"]
        match self.workflow_logic:
            case "pipeline":
                print("pipeline")
                
                if entry_point not in self.functions:
                    print("Entry function is misspelled or not defined")
                else:
                    self.handle_pipeline(self.functions[entry_point])
            case "cron":
                print("cron")
                self.handle_cron(self.functions[entry_point])
            case "one-to_many":
                print("one-to-many")
            case "many-to-one":
                print("many-to-one")
            case "branching":
                print("branching")
            case _:
                print("error")
    
    def deploy_functions(self):
        # Pass functions dict to the OpenFaaS build/deployment function
        build_openfaas_stack(self.functions)


if __name__ == "__main__":
    processor = WorkflowProcessor("../templates/sample_template.yml")
    processor.process_workflow()
