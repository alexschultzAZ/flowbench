import os
import subprocess
import yaml
from datetime import datetime, timezone
import multiprocessing
import math
import time
import requests
from prometheus_api_client import PrometheusConnect
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from knative_deployment import build_and_deploy
import pandas as pd
from prometheus_pandas import query
import pushtogdrive


class WorkflowProcessor:
    def __init__(self, file_path):
        self.template_path = file_path
        self.functions = []
        self.execution_order = {}
        self.workflow_logic_data = {}
        self.workflow_logic = ""
        self.load_template(file_path=file_path)
        self.build_execution_order()
        # self.build_and_deploy_functions()
        # InfluxDB configuration
        # Update if your InfluxDB endpoint is different
        url = "http://localhost:8086"
        # token = "HsVegDZ9D7ZOrbJBcv5IqzfrkhtyvdIR7Zde8qzyJI4hjgZpg87ffsG3yt7cBHAvzCHohSdYVXoivmL22jJlXQ=="           # Replace with your InfluxDB API token
        # self.org = "testorg"                        # Replace with your organization name
        # self.bucket = "testbucket"                  # Replace with the bucket name you want to write data to
        # Replace with your InfluxDB API token
        token = "cYdU0evPogU3_-2gmUBA72U3saY_666UsSh6-zXM8nr_8WHPbNXmCp-cNCPP2JqmCN3ON8Vy-Vgv8koDfYQbGQ=="
        self.org = "test"                        # Replace with your organization name
        # Replace with the bucket name you want to write data to    #CHANGE ALL THE ABOVE STUFF PER MACHINE
        self.bucket = "test"

        # Create a client instance
        self.client = InfluxDBClient(
            url=url, token=token, org=self.org, timeout=30000)

        # Get the write API
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.read_api = self.client.query_api()

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

    def handle_pipeline(self):  # WIP NEEDS ATTENTION
        # prevResponse = {"bucketName" : "stage0", "fileName" : "test_00.mp4"}

        start_time = time.time()

        for __, func_list in self.execution_order.items():
            func = func_list[0]
            input_data = func['data']
            if (len(func_list) > 1):
                print(
                    "Pipeline workflow cannot have two or more functions at the same level")
                return

            service_url = get_knative_service_url(func['name'])
            # Call the knative function/service
            response = requests.post(service_url, json=input_data)
            print("Response =", response.text)
            input_data = response.text
            print("Called " + func['name'])
            break

        pipeline_end_to_end_time = time.time() - start_time
        point = (
            Point("end_to_end_time")               # measurement name
            # .tag("frame", str(frame))          # optional tag
            .tag("invoc", str(0))
            # field value
            .field("end_to_end_time", pipeline_end_to_end_time)
            # current UTC timestamp
            .time(datetime.utcnow(), WritePrecision.NS)
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        print(pipeline_end_to_end_time)

    def stress(self, input_tuple):
        invoc_iter = input_tuple[0]
        invoc_count = input_tuple[1]
        concurrent_fns = 3
        time_between_concurrent_fns = 2
        sleeptime = math.ceil(
            (invoc_iter-1) / concurrent_fns) * time_between_concurrent_fns
        # print("iter: " + str(invoc_iter) + f" sleeping {sleeptime}")
        time.sleep(sleeptime)
        pipeline_start_time = time.time()
        input_data = None
        exception_encountered = False
        metric_points = []
        for __, func_list in self.execution_order.items():
            func = func_list[0]
            if input_data is None:
                input_data = func['data']
            if (len(func_list) > 1):
                print(
                    "Pipeline workflow cannot have two or more functions at the same level")
                return
            try:
                service_url = get_knative_service_url(func['name'])
                req_time = time.time()
                response = requests.post(service_url, json=input_data)
                input_data = response.json()
                func_time = time.time() - req_time
                point = (
                    Point("func_time")               # measurement name
                    .tag("func_name", str(func['name']))
                    .tag("invoc_count", str(invoc_count))
                    .tag("invoc", str(invoc_iter))
                    .field("func_time", func_time)         # field value
                    # current UTC timestamp
                    .time(datetime.utcnow().isoformat())
                )
                metric_points.append(point)
            except Exception as e:
                exception_encountered = True
                print("exception encountered calling " +
                      str(service_url) + " " + str(invoc_iter) + ": " + str(e))

        if not exception_encountered:
            pipeline_end_to_end_time = time.time() - pipeline_start_time
            print("iter: " + str(invoc_iter) + " took " +
                  str(pipeline_end_to_end_time))
            point = (
                Point("end_to_end_time")               # measurement name
                # .tag("frame", str(frame))          # optional tag
                .tag("invoc_count", str(invoc_count))
                .tag("invoc", str(invoc_iter))
                # field value
                .field("end_to_end_time", pipeline_end_to_end_time)
                .time(datetime.utcnow().isoformat())  # current UTC timestamp
            )
            metric_points.append(point)
        return metric_points
    
    
    def get_prom_to_csv(self, prom, qr, stress_start_time_strf, stress_stop_time_strf):
        
        cpu_per_pod = prom.query_range(qr, stress_start_time_strf, stress_stop_time_strf, '1s')
        
        init_split = cpu_per_pod.to_csv().split("\n")
        cpu_per_pod_split = []
        for row in init_split:
            cpu_per_pod_split.append(row.split(","))
        
        new_first_line = [cpu_per_pod_split[0][1]]
        for cell in cpu_per_pod_split[0]:
            if "pod=" in cell:
                new_first_line.append(cell)
        massaged_list = [new_first_line]
        for row in cpu_per_pod_split[1:]:
            massaged_list.append(row)
        
        return massaged_list
        

    def stress_pipeline(self, invoc_count):
        stress_start_time = datetime.now(timezone.utc)
        stress_start_time_strf = stress_start_time.strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-4] + "Z"

        invoc_count = int(invoc_count)
        pool = multiprocessing.Pool()
        pool = multiprocessing.Pool(processes=invoc_count)
        invoc_iter = list(range(1, invoc_count+1))
        invoc_count = [invoc_count] * invoc_count
        input_list_tuples = [(x, y) for x, y in zip(invoc_iter, invoc_count)]

        outputs = pool.map(self.stress, input_list_tuples)
        if outputs is not None:
            for output in outputs:
                self.write_api.write(
                    bucket=self.bucket, org=self.org, record=output, write_precision="ms")

        stress_stop_time = datetime.now(timezone.utc)
        stress_stop_time_strf = stress_stop_time.strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-4] + "Z"

        #################### METRICS ###############################
        # query influxdb
        queries = [
            'from(bucket: "' + str(self.bucket) + '") \
                    |> range(start: ' + stress_start_time_strf + ', stop: ' + stress_stop_time_strf + ') \
                    |> filter(fn: (r) => r["_measurement"] == "end_to_end_time") \
                    |> filter(fn: (r) => r["_field"] == "end_to_end_time")',
            'from(bucket: "' + str(self.bucket) + '") \
                    |> range(start: ' + stress_start_time_strf + ', stop: ' + stress_stop_time_strf + ') \
                    |> filter(fn: (r) => r["_measurement"] == "func_time") \
                    |> filter(fn: (r) => r["_field"] == "func_time")'
        ]

        csv_master = []
        for qr in queries:
            csv_master.append(self.read_api.query_csv(qr).to_values())

        
        
        # query promtheus
        prom = query.Prometheus("http://localhost:9090") # only works if port forwarding is on
        # FaaS
        # prom_queries = [
        #     'sum (rate (container_cpu_usage_seconds_total{pod=~"vidsplit.*|modect.*|facerec.*|facextract.*", container="user-container"}[60s])) / sum (machine_cpu_cores) * 100',
        #     'node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{pod=~"vidsplit.*|modect.*|facerec.*|facextract.*", container="user-container"}',
        #     'container_network_transmit_bytes_total{pod=~"vidsplit.*|modect.*|facerec.*|facextract.*"}',
        #     'container_memory_usage_bytes{pod=~"vidsplit.*|modect.*|facerec.*|facextract.*", container="user-container"}',
        #     'DCGM_FI_DEV_GPU_UTIL'
        # ]
        # monolith
        prom_queries = [
            'sum (rate (container_cpu_usage_seconds_total{pod=~"va-monolith.*", container="user-container"}[60s])) / sum (machine_cpu_cores) * 100',
            'node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{pod=~"va-monolith.*", container="user-container"}',
            'container_network_transmit_bytes_total{pod=~"va-monolith.*"}',
            'container_memory_usage_bytes{pod=~"va-monolith.*", container="user-container"}',
            'DCGM_FI_DEV_GPU_UTIL'
        ]
        
        for qr in prom_queries:
            try:
                csv_master.append(self.get_prom_to_csv(prom, qr, stress_start_time, stress_stop_time))
            except Exception as e:
                print("Error pulling from prom: " + str(qr))
        
        pushtogdrive.push_to_drive(csv_master)

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
        print("Total \'many\' function count = {}, next_function = {}".format(
            functions_count, next_function))
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
                print(
                    f"Request failed with status code: {response.status_code}")

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
                    raise ValueError(
                        f"Invalid integer comparison between {result} and {operand}")

            elif conditions['type'] == "boolean_comparison":
                try:
                    if type(result) == 'string':
                        result = result.lower() == 'true'
                    if type(operand) == 'string':
                        operand = bool(operand)
                except ValueError:
                    raise ValueError(
                        f"Invalid boolean comparison between {result} and {operand}")

            condition_met = False
            expression = f'{operand} {operator} {result}'
            try:
                condition_met = eval(expression)
                print("Condition met is ", condition_met)
            except ValueError:
                raise ValueError(f"Invalid operator: {operator}")

            next_func = true_func if condition_met else false_func
            response = requests.get(
                f"http://127.0.0.1:8080/function/{next_func}")
            if response.status_code == 200:
                print(f"Request was successful for {next_func}")
            else:
                print(
                    f"Request failed for {next_func} with status code: {response.status_code}")
        else:
            print(
                f"Request failed for {entry_func} with status code: {response.status_code}")

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

    def stress_workflow(self, invoc_count):
        if self.workflow_logic == "pipeline":
            print("pipeline")
            self.stress_pipeline(invoc_count)
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
        print("building...")
        build_and_deploy(self.functions)


def get_knative_service_url(service_name):
    try:
        # Run the kubectl command to get the name and URL of the service
        result = subprocess.run(
            ['microk8s', 'kubectl', 'get', 'ksvc', service_name,
                '--output=custom-columns=NAME:.metadata.name,URL:.status.url'],
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
        # print(url)
        return url
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description='Process a workflow template file.')

#     # Add the argument for the template file
#     parser.add_argument('template_file', type=str,
#                         help='Path to the workflow template file')

#     # Parse the arguments
#     args = parser.parse_args()

#     # Create the WorkflowProcessor instance with the provided file name
#     processor = WorkflowProcessor(args.template_file)
#     processor.build_and_deploy_functions()
#     processor.process_workflow()
#     self.client.close()
